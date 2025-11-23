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
      console.error('[v0] Failed to load bids:', error);
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
          {Array.isArray(bids) && bids.length > 0 ? (
            bids.map((bid) => (
              <Card key={bid.id}>
                <CardHeader>
                  <div className="flex items-start justify-between">
                    <div>
                      <CardTitle>Auction #{bid.auction_id}</CardTitle>
                      <CardDescription>
                        Placed on {new Date(bid.created_at).toLocaleString()}
                      </CardDescription>
                    </div>
                    <p className="text-xl font-bold">
                      ${(bid.amount / 100).toFixed(2)}
                    </p>
                  </div>
                </CardHeader>
                <CardContent>
                  <Link href={`/auction/${bid.auction_id}`}>
                    <Button variant="outline">View Auction</Button>
                  </Link>
                </CardContent>
              </Card>
            ))
          ) : (
            <p className="text-center text-muted-foreground py-4">No bids found</p>
          )}
        </div>
      )}
    </div>
  );
}
