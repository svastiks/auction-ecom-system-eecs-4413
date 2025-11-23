'use client';

import { useState, useEffect } from 'react';
import { api, Auction, Item, ApiError } from '@/lib/api';
import { useAuth } from '@/lib/auth-context';
import { Button } from '@/components/ui/button';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { useToast } from '@/hooks/use-toast';
import { ArrowLeft, Package } from 'lucide-react';
import Link from 'next/link';
import { useRouter, useParams } from 'next/navigation';

export default function ItemAuctionsPage() {
  const { user, isLoading: authLoading } = useAuth();
  const router = useRouter();
  const { toast } = useToast();
  const params = useParams<{ id: string }>();

  console.log("Params object:", params);

  const id = params?.id;

  const [auctions, setAuctions] = useState<Auction[]>([]);
  const [item, setItem] = useState<Item | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // Redirect unauthenticated users
  useEffect(() => {
    if (!authLoading && !user) {
      router.push('/auth');
    }
  }, [authLoading, user, router]);

  // Load data when ID changes
  useEffect(() => {
    if (!id) {
      console.error('No item ID provided');
      return;
    }
    console.log('Loading data for item:', id);
    loadData(id);
  }, [id]);

  const loadData = async (itemId: string) => {
    setIsLoading(true);

    console.log('Loading data for item:', itemId);

    try {
      const [auctionsData, itemData] = await Promise.all([
        api.getItemAuctions(Number(itemId)),
        api.getItem(Number(itemId)),
      ]);
      setAuctions(Array.isArray(auctionsData) ? auctionsData : []);
      setItem(itemData || null);
    } catch (error) {
      console.error('[ItemAuctionsPage] Failed to load data:', error);
      const message =
        error instanceof ApiError ? error.message : 'Failed to load data';
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
        <p className="text-center text-muted-foreground">Loading...</p>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-8 max-w-4xl">
      <Link href="/catalogue">
        <Button variant="ghost" className="mb-6">
          <ArrowLeft className="h-4 w-4 mr-2" />
          Back to Catalogue
        </Button>
      </Link>

      {item && (
        <div className="mb-8">
          <h1 className="text-3xl font-bold mb-2">
            Auctions for: {item.title}
          </h1>
          <p className="text-muted-foreground">{item.description}</p>
        </div>
      )}

      {Array.isArray(auctions) && auctions.length > 0 ? (
        <div className="space-y-4">
          {auctions.map((auction) => {
            const currentHighest =
              auction.current_highest_bid || auction.starting_price;
            const endTime = new Date(auction.end_time);
            const hasEnded =
              endTime <= new Date() || auction.status === 'ENDED';

            return (
              <Card key={auction.id ?? Math.random()}>
                <CardHeader>
                  <div className="flex items-start justify-between">
                    <div>
                      <CardTitle>Auction #{auction.id}</CardTitle>
                      <CardDescription>
                        {hasEnded ? 'Ended' : 'Ends'} on{' '}
                        {endTime.toLocaleString()}
                      </CardDescription>
                    </div>
                    <Badge variant={hasEnded ? 'secondary' : 'default'}>
                      {hasEnded ? 'ENDED' : auction.status}
                    </Badge>
                  </div>
                </CardHeader>

                <CardContent>
                  <div className="flex items-center justify-between">
                    <div className="space-y-1">
                      <p className="text-sm text-muted-foreground">
                        Current Highest Bid
                      </p>
                      <p className="text-2xl font-bold">
                        ${(currentHighest / 100).toFixed(2)}
                      </p>
                      <p className="text-xs text-muted-foreground">
                        Starting: ${(auction.starting_price / 100).toFixed(2)} |
                        Min increment:
                        ${(auction.min_increment / 100).toFixed(2)}
                      </p>
                    </div>

                    <Link href={`/auction/${auction.id}`}>
                      <Button>
                        {hasEnded ? 'View Results' : 'View & Bid'}
                      </Button>
                    </Link>
                  </div>
                </CardContent>
              </Card>
            );
          })}
        </div>
      ) : (
        <div className="text-center py-12">
          <Package className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
          <h3 className="text-lg font-semibold mb-2">No auctions found</h3>
          <p className="text-muted-foreground mb-4">
            There are no active auctions for this item yet.
          </p>
          <Link href="/seller/create-auction">
            <Button>Create Auction</Button>
          </Link>
        </div>
      )}
    </div>
  );
}