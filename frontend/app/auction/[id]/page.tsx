'use client';

import { useState, useEffect } from 'react';
import { api, Auction, Bid, ApiError } from '@/lib/api';
import { useParams } from "next/navigation";
import { useAuth } from '@/lib/auth-context';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { useToast } from '@/hooks/use-toast';
import { ArrowLeft, Clock, Gavel, TrendingUp } from 'lucide-react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useAuctionTimer } from '@/lib/use-auction-timer';

export default function AuctionDetailPage() {
  const { user, isLoading: authLoading } = useAuth();
  const router = useRouter();
  const { toast } = useToast();
  const params = useParams();
  const [auction, setAuction] = useState<Auction | null>(null);
  const [bids, setBids] = useState<Bid[]>([]);
  const [bidAmount, setBidAmount] = useState('');
  const [isLoading, setIsLoading] = useState(true);
  const [isPlacingBid, setIsPlacingBid] = useState(false);
  const timeRemaining = useAuctionTimer(auction?.end_time || '');

  useEffect(() => {
    if (!authLoading && !user) {
      router.push('/auth');
    }
  }, [user, authLoading, router]);

  useEffect(() => {
    if (!params?.id) return;
    loadAuctionData();
  }, [params?.id]);

  useEffect(() => {
    if (!auction || auction.status !== 'ACTIVE') return;

    const interval = setInterval(() => {
      loadAuctionData();
    }, 10000); // Poll every 10 seconds

    return () => clearInterval(interval);
  }, [auction?.status, params.id]);

  const loadAuctionData = async () => {
    if (!params?.id || params.id === 'undefined') {
      setIsLoading(false);
      return;
    }
    
    try {
      const auctionId = params.id as string; // UUID is a string, not a number
      const [auctionData, bidsData] = await Promise.all([
        api.getAuction(auctionId),
        api.getAuctionBids(auctionId),
      ]);
      setAuction(auctionData);
      setBids(bidsData);
      
      // Set suggested bid amount
      const currentHighest = auctionData.current_highest_bid || auctionData.starting_price;
      const minBid = currentHighest + auctionData.min_increment;
      setBidAmount((minBid / 100).toFixed(2));
    } catch (error) {
      console.error('Failed to load auction:', error);
      const message = error instanceof ApiError ? error.message : 'Failed to load auction';
      toast({
        title: 'Error',
        description: message,
        variant: 'destructive',
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handlePlaceBid = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!auction) return;

    const amount = Math.round(parseFloat(bidAmount) * 100);

    if (isNaN(amount)) {
      toast({
        title: 'Validation Error',
        description: 'Please enter a valid bid amount',
        variant: 'destructive',
      });
      return;
    }

    const currentHighest = auction.current_highest_bid || auction.starting_price;
    const minBid = currentHighest + auction.min_increment;

    if (amount < minBid) {
      toast({
        title: 'Validation Error',
        description: `Bid must be at least $${(minBid / 100).toFixed(2)}`,
        variant: 'destructive',
      });
      return;
    }

    setIsPlacingBid(true);

    try {
      const auctionId = auction.id || (auction as any).auction_id || params?.id;
      if (!auctionId) {
        throw new Error('Auction ID is missing');
      }
      await api.placeBid(auctionId as string, amount);
      
      toast({
        title: 'Success',
        description: 'Bid placed successfully',
      });
      
      // Reload auction data
      await loadAuctionData();
    } catch (error) {
      console.error('Failed to place bid:', error);
      let errorMessage = 'Failed to place bid';
      
      if (error instanceof ApiError) {
        // Try multiple ways to extract the error message
        errorMessage = 
          error.message || 
          error.data?.detail || 
          error.data?.message || 
          (error.data && typeof error.data === 'string' ? error.data : null) ||
          `Error ${error.status}: ${error.status === 400 ? 'Bad Request' : error.status === 401 ? 'Unauthorized' : error.status === 404 ? 'Not Found' : error.status === 500 ? 'Server Error' : 'Unknown Error'}`;
      } else if (error instanceof Error) {
        errorMessage = error.message || 'An unexpected error occurred';
      } else if (typeof error === 'string') {
        errorMessage = error;
      }
      
      // Ensure we always have a message
      if (!errorMessage || errorMessage.trim() === '') {
        errorMessage = 'Failed to place bid. Please try again.';
      }
      
      toast({
        title: 'Error',
        description: errorMessage,
        variant: 'destructive',
      });
    } finally {
      setIsPlacingBid(false);
    }
  };

  if (authLoading || isLoading) {
    return (
      <div className="container mx-auto px-4 py-8">
        <p className="text-center text-muted-foreground">Loading auction...</p>
      </div>
    );
  }

  if (!auction) {
    return (
      <div className="container mx-auto px-4 py-8">
        <p className="text-center text-muted-foreground">Auction not found</p>
      </div>
    );
  }

  const currentHighest = auction.current_highest_bid || auction.starting_price;
  const hasEnded = auction.status === 'ENDED' || timeRemaining.isEnded;
  const isWinner = hasEnded && auction.winning_bidder_id === user?.id;
  console.log(auction);
  console.log(user?.id);
  const hasOrder = auction.has_order || false;
  const isSold = hasOrder;

  return (
    <div className="container mx-auto px-4 py-8 max-w-5xl">
      <Link href="/catalogue">
        <Button variant="ghost" className="mb-6">
          <ArrowLeft className="h-4 w-4 mr-2" />
          Back to Catalogue
        </Button>
      </Link>

      <div className="grid lg:grid-cols-3 gap-6">
        {/* Main Content */}
        <div className="lg:col-span-2 space-y-6">
          {/* Item Info */}
          {auction.item && (
            <Card>
              <div className="aspect-video bg-muted relative">
                {auction.item.images && auction.item.images.length > 0 ? (
                  <img
                    src={auction.item.images[0].url || "/placeholder.svg"}
                    alt={auction.item.title}
                    className="w-full h-full object-cover"
                  />
                ) : null}
              </div>
              <CardHeader>
                <CardTitle>{auction.item.title}</CardTitle>
                <CardDescription>{auction.item.description}</CardDescription>
              </CardHeader>
            </Card>
          )}

          {/* Bid History */}
          <Card>
            <CardHeader>
              <CardTitle>Bid History</CardTitle>
              <CardDescription>{bids.length} bids placed</CardDescription>
            </CardHeader>
            <CardContent>
              {bids.length === 0 ? (
                <p className="text-center text-muted-foreground py-4">No bids yet</p>
              ) : (
                <div className="space-y-3">
                  {bids.map((bid, index) => (
                    <div
                      key={bid.id}
                      className="flex items-center justify-between p-3 rounded-lg border"
                    >
                      <div className="flex items-center gap-3">
                        {index === 0 && (
                          <TrendingUp className="h-4 w-4 text-primary" />
                        )}
                        <div>
                          <p className="font-medium">
                            ${(bid.amount / 100).toFixed(2)}
                          </p>
                          <p className="text-sm text-muted-foreground">
                            {bid.bidder?.first_name && bid.bidder?.last_name
                              ? `${bid.bidder.first_name} ${bid.bidder.last_name}`
                              : bid.user?.first_name && bid.user?.last_name
                              ? `${bid.user.first_name} ${bid.user.last_name}`
                              : bid.user?.username || 'Unknown user'}
                          </p>
                        </div>
                      </div>
                      <p className="text-xs text-muted-foreground">
                        {bid.created_at ? new Date(bid.created_at).toLocaleString() : 'Unknown date'}
                      </p>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Sidebar */}
        <div className="space-y-4">
          {/* Status Card */}
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle className="text-lg">Auction Status</CardTitle>
                <Badge variant={hasEnded ? 'secondary' : 'default'}>
                  {hasEnded ? 'ENDED' : auction.status}
                </Badge>
              </div>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <p className="text-sm text-muted-foreground mb-1">Current Highest Bid</p>
                <p className="text-2xl font-bold">
                  ${(currentHighest / 100).toFixed(2)}
                </p>
              </div>

              {!hasEnded && (
                <div className="p-4 bg-muted rounded-lg">
                  <div className="flex items-center gap-2 mb-2">
                    <Clock className="h-4 w-4" />
                    <p className="text-sm font-medium">Time Remaining</p>
                  </div>
                  <div className="grid grid-cols-4 gap-2 text-center">
                    <div>
                      <p className="text-2xl font-bold">{timeRemaining.days}</p>
                      <p className="text-xs text-muted-foreground">Days</p>
                    </div>
                    <div>
                      <p className="text-2xl font-bold">{timeRemaining.hours}</p>
                      <p className="text-xs text-muted-foreground">Hours</p>
                    </div>
                    <div>
                      <p className="text-2xl font-bold">{timeRemaining.minutes}</p>
                      <p className="text-xs text-muted-foreground">Mins</p>
                    </div>
                    <div>
                      <p className="text-2xl font-bold">{timeRemaining.seconds}</p>
                      <p className="text-xs text-muted-foreground">Secs</p>
                    </div>
                  </div>
                </div>
              )}

              {hasEnded && isSold && (
                <div className="p-4 bg-muted rounded-lg border text-center">
                  <p className="font-semibold mb-2">Item Sold</p>
                  <p className="text-sm text-muted-foreground">
                    This item has been sold for ${(currentHighest / 100).toFixed(2)}
                  </p>
                  {isWinner && auction.order_id && (
                    <Link href={`/order/${auction.order_id}/receipt`} className="mt-3 inline-block">
                      <Button variant="outline" size="sm">
                        View Order
                      </Button>
                    </Link>
                  )}
                </div>
              )}

              {hasEnded && isWinner && !isSold && (
                <div className="p-4 bg-primary/10 rounded-lg border border-primary">
                  <p className="text-center font-semibold mb-3 text-primary">
                    🎉 You won this auction!
                  </p>
                  <Link href={`/order/create?auction=${auction.id}`}>
                    <Button className="w-full">
                      Pay Now
                    </Button>
                  </Link>
                </div>
              )}

              {hasEnded && !isWinner && !isSold && (
                <div className="p-4 bg-muted rounded-lg text-center">
                  <p className="text-muted-foreground">
                    Auction ended. You did not win.
                  </p>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Bidding Form */}
          {!hasEnded && (
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Place Your Bid</CardTitle>
                <CardDescription>
                  Min increment: ${(auction.min_increment / 100).toFixed(2)}
                </CardDescription>
              </CardHeader>
              <CardContent>
                <form onSubmit={handlePlaceBid} className="space-y-4">
                  <div className="space-y-2">
                    <Label htmlFor="bid-amount">Bid Amount ($)</Label>
                    <Input
                      id="bid-amount"
                      type="number"
                      step="0.01"
                      min={(currentHighest + auction.min_increment) / 100}
                      required
                      value={bidAmount}
                      onChange={(e) => setBidAmount(e.target.value)}
                    />
                    <p className="text-xs text-muted-foreground">
                      Minimum bid: ${((currentHighest + auction.min_increment) / 100).toFixed(2)}
                    </p>
                  </div>
                  <Button type="submit" className="w-full" disabled={isPlacingBid}>
                    <Gavel className="h-4 w-4 mr-2" />
                    {isPlacingBid ? 'Placing Bid...' : 'Place Bid'}
                  </Button>
                </form>
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
}
