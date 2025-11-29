'use client';

import React, { useEffect, useState } from 'react';
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
import { useRouter } from 'next/navigation';

export default function ItemAuctionsPage({
  params,
}: {
  params: Promise<{ id?: string }>;
}) {
  // Unwrap Next.js 15 async params
  const { id } = React.use(params);

  const { user, isLoading: authLoading } = useAuth();
  const router = useRouter();
  const { toast } = useToast();

  const [auctions, setAuctions] = useState<Auction[]>([]);
  const [item, setItem] = useState<Item | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    if (!authLoading && !user) {
      router.push('/auth');
    }
  }, [user, authLoading, router]);

  useEffect(() => {
    if (!id || id === 'undefined') {
      setIsLoading(false);
      return;
    }

    const loadData = async () => {
      setIsLoading(true);
      try {
        const [auctionsResp, itemData] = await Promise.all([
          // IMPORTANT: pass id as string (can be UUID)
          api.getItemAuctions(id as string),
          api.getItem(id as string),
        ]);

        // Normalize auctions to an array regardless of backend shape
        const auctionsArr: Auction[] = Array.isArray(auctionsResp)
          ? auctionsResp
          : Array.isArray((auctionsResp as any)?.data)
          ? (auctionsResp as any).data
          : auctionsResp == null
          ? []
          : [auctionsResp as unknown as Auction];

        setAuctions(auctionsArr);
        setItem(itemData);
      } catch (error) {
        console.error('[item-auctions] Failed to load data:', error);
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

    loadData();
  }, [id, toast]);

  if (authLoading || isLoading) {
    return (
      <div className="container mx-auto px-4 py-8">
        <p className="text-center text-muted-foreground">Loading...</p>
      </div>
    );
  }

  if (!item) {
    return (
      <div className="container mx-auto px-4 py-16 max-w-2xl text-center">
        <h1 className="text-2xl font-semibold mb-2">Item not found</h1>
        <p className="text-muted-foreground mb-6">
          We couldn’t find that item or it may have been removed.
        </p>
        <Link href="/catalogue">
          <Button>Back to Catalogue</Button>
        </Link>
      </div>
    );
  }

  const auctionsSafe = Array.isArray(auctions) ? auctions : [];

  return (
    <div className="container mx-auto px-4 py-8 max-w-4xl">
      <Link href="/catalogue">
        <Button variant="ghost" className="mb-6">
          <ArrowLeft className="h-4 w-4 mr-2" />
          Back to Catalogue
        </Button>
      </Link>

      <div className="mb-8">
        <h1 className="text-3xl font-bold mb-2">Auctions for: {item.title}</h1>
        <p className="text-muted-foreground">{item.description}</p>
      </div>

      {auctionsSafe.length === 0 ? (
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
      ) : (
        <div className="space-y-4">
          {auctionsSafe.map((auction) => {
            const currentHighest =
              auction.current_highest_bid || auction.starting_price;
            const endTime = new Date(auction.end_time);
            const hasEnded =
              endTime <= new Date() || auction.status === 'ENDED';

            return (
              <Card key={auction.id}>
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
                        Starting: ${(auction.starting_price / 100).toFixed(2)} | Min
                        increment: ${(auction.min_increment / 100).toFixed(2)}
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
      )}
    </div>
  );
}
