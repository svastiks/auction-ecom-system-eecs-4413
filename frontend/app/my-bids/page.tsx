'use client';

import { useState, useEffect } from 'react';
import { api, Bid, ApiError } from '@/lib/api';
import { useAuth } from '@/lib/auth-context';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { useToast } from '@/hooks/use-toast';
import { Gavel } from 'lucide-react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';

export default function MyBidsPage() {
  const { user, isLoading: authLoading } = useAuth();
  const router = useRouter();
  const { toast } = useToast();
  const [bids, setBids] = useState<Bid[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    if (!authLoading && !user) {
      router.push('/auth');
    }
  }, [user, authLoading, router]);

  useEffect(() => {
    loadBids();
  }, []);

  const loadBids = async () => {
    setIsLoading(true);
    try {
      const bidsData = await api.getMyBids();
      setBids(bidsData);
    } catch (error) {
      console.error('Failed to load bids:', error);
      const message = error instanceof ApiError ? error.message : 'Failed to load bids';
      toast({
        title: 'Error',
        description: message,
        variant: 'destructive',
      });
    } finally {
      setIsLoading(false);
    }
  };

  if (authLoading || isLoading) {
    return (
      <div className="container mx-auto px-4 py-8">
        <p className="text-center text-muted-foreground">Loading bids...</p>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-8">
      <h1 className="text-3xl font-bold mb-8">My Bids</h1>

      {bids.length === 0 ? (
        <div className="text-center py-12">
          <Gavel className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
          <h3 className="text-lg font-semibold mb-2">No bids yet</h3>
          <p className="text-muted-foreground mb-4">
            Start bidding on auctions to see your bids here
          </p>
          <Link href="/catalogue">
            <Button>Browse Auctions</Button>
          </Link>
        </div>
      ) : (
        <div className="space-y-4">
          {bids.map((bid) => {
            const bidId = bid.id || bid.bid_id || String(Math.random());
            const auctionId = bid.auction_id || '';
            const bidAmount = bid.amount || bid.last_bid_amount || 0;
            const bidDate = bid.created_at || bid.placed_at || new Date().toISOString();
            const itemTitle = bid.item_title || 'Auction Item';
            
            return (
              <Card key={bidId}>
                <CardHeader>
                  <div className="flex items-start justify-between">
                    <div>
                      <CardTitle>{itemTitle}</CardTitle>
                      <CardDescription>
                        {bid.status && (
                          <span className={`mr-2 px-2 py-1 rounded text-xs ${
                            bid.status === 'LEADING' ? 'bg-green-100 text-green-800' :
                            bid.status === 'OUTBID' ? 'bg-yellow-100 text-yellow-800' :
                            bid.status === 'WON' ? 'bg-blue-100 text-blue-800' :
                            'bg-gray-100 text-gray-800'
                          }`}>
                            {bid.status}
                          </span>
                        )}
                        Placed on {new Date(bidDate).toLocaleString()}
                      </CardDescription>
                    </div>
                    <div className="text-right">
                      <p className="text-xl font-bold">${(bidAmount / 100).toFixed(2)}</p>
                      {bid.current_highest_bid && bid.current_highest_bid !== bidAmount && (
                        <p className="text-sm text-muted-foreground">
                          Highest: ${(bid.current_highest_bid / 100).toFixed(2)}
                        </p>
                      )}
                    </div>
                  </div>
                </CardHeader>
                <CardContent>
                  <Link href={`/auction/${auctionId}`}>
                    <Button variant="outline">View Auction</Button>
                  </Link>
                </CardContent>
              </Card>
            );
          })}
        </div>
      )}
    </div>
  );
}
