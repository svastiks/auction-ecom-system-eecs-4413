'use client';

import type React from 'react';

import { useState, useEffect } from 'react';
import { api, type Item, type Category, type Auction, ApiError } from '@/lib/api';
import { useAuth } from '@/lib/auth-context';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { useToast } from '@/hooks/use-toast';
import { Search, Package } from 'lucide-react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';

type ViewFilter = 'all' | 'active' | 'ended' | 'my-auctions';

export default function CataloguePage() {
  const { user, isLoading: authLoading } = useAuth();
  const router = useRouter();
  const { toast } = useToast();
  const [items, setItems] = useState<Item[]>([]);
  const [allAuctions, setAllAuctions] = useState<Auction[]>([]);
  const [categories, setCategories] = useState<Category[]>([]);
  const [searchKeyword, setSearchKeyword] = useState('');
  const [isLoading, setIsLoading] = useState(true);
  const [isSearching, setIsSearching] = useState(false);
  const [viewFilter, setViewFilter] = useState<ViewFilter>('all');

  useEffect(() => {
    if (!authLoading && !user) {
      router.push('/auth');
    }
  }, [user, authLoading, router]);

  useEffect(() => {
    loadData();
  }, []);

  const normalizeItems = (arr: any[]): Item[] =>
    arr.map((it: any) => ({
      ...it,
      // Ensure id is always present for routing
      id: it.id ?? it.item_id ?? it.itemId,
    }));

  const loadData = async () => {
    setIsLoading(true);
    try {
      // Get items and categories
      const [itemsData, categoriesData] = await Promise.all([
        api.getItems(),
        api.getCategories(),
      ]);

      const normalizedItems = normalizeItems(itemsData as any[]);
      setItems(normalizedItems);
      setCategories(categoriesData);

      // For each item with an auction_id, fetch the auction details to build allAuctions
      const auctionPromises = normalizedItems
        .filter(item => item.auction_id)
        .map(item =>
          api.getAuction(item.auction_id!)
            .then(auction => ({ ...auction, item }))
            .catch(err => {
              console.error(`Failed to load auction ${item.auction_id}:`, err);
              return null;
            })
        );

      const auctionsData = await Promise.all(auctionPromises);
      const validAuctions = auctionsData.filter(a => a !== null);
      setAllAuctions(validAuctions as any[]);
    } catch (error) {
      console.error('Failed to load catalogue:', error);
      const message =
        error instanceof ApiError ? error.message : 'Failed to load catalogue';
      toast({
        title: 'Error',
        description: message,
        variant: 'destructive',
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!searchKeyword.trim()) {
      loadData();
      return;
    }

    setIsSearching(true);
    try {
      const searchResponse = await api.searchAuctions(searchKeyword);

      // The search response returns AuctionSearchResponse with items array
      const auctionSummaries = (searchResponse as any).items || [];

      if (auctionSummaries.length === 0) {
        setItems([]);
        setAllAuctions([]);
        toast({
          title: 'No results',
          description: 'No items found matching your search',
        });
        return;
      }

      // Convert AuctionItemSummary objects to items format
      const searchedItems = auctionSummaries.map((summary: any) => {
        console.log('Processing summary:', summary);
        console.log('Current bidding price:', summary.current_bidding_price, 'Type:', typeof summary.current_bidding_price);

        // The price comes as cents from backend, need to keep it as cents
        const basePrice = typeof summary.current_bidding_price === 'string'
          ? parseFloat(summary.current_bidding_price)
          : Number(summary.current_bidding_price) || 0;

        console.log('Converted base price:', basePrice);

        return {
          id: summary.item_id,
          item_id: summary.item_id,
          auction_id: summary.auction_id,
          title: summary.title,
          description: summary.description,
          base_price: basePrice,
          category_id: 0, // Not provided as ID in summary
          category: {
            name: summary.category_name || 'Uncategorized'
          },
          images: summary.item_images?.map((url: string, idx: number) => ({
            id: idx,
            url,
            position: idx
          })) || [],
          is_active: summary.status === 'ACTIVE',
          shipping_price_normal: 0, // Not in summary
          shipping_price_expedited: 0, // Not in summary
          shipping_time_days: 0, // Not in summary
        };
      });

      setItems(searchedItems);

      // Build auctions array from summaries
      // Use remaining_time_seconds to calculate end_time
      const now = new Date();
      const searchedAuctions = auctionSummaries.map((summary: any) => {
        const endTime = summary.remaining_time_seconds
          ? new Date(now.getTime() + summary.remaining_time_seconds * 1000).toISOString()
          : now.toISOString();

        return {
          auction_id: summary.auction_id,
          id: summary.auction_id,
          end_time: endTime,
          status: summary.status,
          item: {
            item_id: summary.item_id,
            title: summary.title,
            seller_id: null, // Not in summary
          },
          bids: [], // Not in summary
        };
      });
      setAllAuctions(searchedAuctions);

    } catch (error) {
      console.error('Search error:', error);
      const message = error instanceof ApiError ? error.message : 'Search failed';
      toast({
        title: 'Error',
        description: message,
        variant: 'destructive',
      });
    } finally {
      setIsSearching(false);
    }
  };

  // Filter auctions based on the selected view
  const getFilteredItems = (): Item[] => {
    if (!user) return items;

    // If no filter (all auctions), just return items directly
    if (viewFilter === 'all') {
      return items;
    }

    let filteredAuctions = allAuctions;

    switch (viewFilter) {
      case 'active':
        // Active auctions are those that haven't ended yet
        filteredAuctions = allAuctions.filter((auction: any) => {
          const endTime = new Date(auction.end_time);
          return endTime > new Date();
        });
        break;
      case 'ended':
        // Ended auctions are those where end_time has passed
        filteredAuctions = allAuctions.filter((auction: any) => {
          const endTime = new Date(auction.end_time);
          return endTime <= new Date();
        });
        break;
      case 'my-auctions':
        // My auctions = auctions I'm selling (I created)
        filteredAuctions = allAuctions.filter((auction: any) => {
          if (!auction || !user) return false;

          const userId = user.id || user.user_id;
          const sellerId = auction.item?.seller_id;

          // Only check if user is the seller
          const isSeller = !!(sellerId && (sellerId === userId || sellerId === user.user_id));

          return isSeller;
        });
        break;
    }

    // Filter items based on auction IDs
    const filteredAuctionIds = new Set(filteredAuctions.map((a: any) => a.auction_id));
    return items.filter((item) => filteredAuctionIds.has(item.auction_id));
  };

  const getCategoryName = (item: Item) => {
    // If item has category object with name, use it (from search results)
    if (item.category && (item.category as any).name) {
      return (item.category as any).name;
    }
    // Otherwise look up by category_id (from regular catalogue)
    const category = categories.find((c) => c.id === item.category_id);
    return category?.name || 'Uncategorized';
  };

  if (authLoading || isLoading) {
    return (
      <div className="container mx-auto px-4 py-8">
        <p className="text-center text-muted-foreground">Loading catalogue...</p>
      </div>
    );
  }

  const displayedItems = getFilteredItems();

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold mb-4">Item Catalogue</h1>

        <form onSubmit={handleSearch} className="flex gap-2 max-w-xl mb-4">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
            <Input
              type="text"
              placeholder="Search items by keyword..."
              value={searchKeyword}
              onChange={(e) => setSearchKeyword(e.target.value)}
              className="pl-9"
            />
          </div>
          <Button type="submit" disabled={isSearching}>
            {isSearching ? 'Searching...' : 'Search'}
          </Button>
          {searchKeyword && (
            <Button
              type="button"
              variant="outline"
              onClick={() => {
                setSearchKeyword('');
                loadData();
              }}
            >
              Clear
            </Button>
          )}
        </form>

        {/* View Filter Buttons */}
        <div className="flex gap-2 flex-wrap">
          <Button
            variant={viewFilter === 'all' ? 'default' : 'outline'}
            onClick={() => setViewFilter('all')}
          >
            All Auctions
          </Button>
          <Button
            variant={viewFilter === 'active' ? 'default' : 'outline'}
            onClick={() => setViewFilter('active')}
          >
            Active Auctions
          </Button>
          <Button
            variant={viewFilter === 'ended' ? 'default' : 'outline'}
            onClick={() => setViewFilter('ended')}
          >
            Ended Auctions
          </Button>
          <Button
            variant={viewFilter === 'my-auctions' ? 'default' : 'outline'}
            onClick={() => setViewFilter('my-auctions')}
          >
            My Auctions
          </Button>
        </div>
      </div>

      {displayedItems.length === 0 ? (
        <div className="text-center py-12">
          <Package className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
          <h3 className="text-lg font-semibold mb-2">No items found</h3>
          <p className="text-muted-foreground mb-4">
            {searchKeyword ? 'Try a different search term' : 'No items are available yet'}
          </p>
          <Link href="/seller/create-auction">
            <Button>Create First Auction</Button>
          </Link>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {displayedItems.map((item) => {
            console.log('Rendering item:', item.title, 'base_price:', item.base_price, 'type:', typeof item.base_price);
            const hasId = item.id != null;
            return (
              <Card key={`${item.id ?? item.title}-${item.category_id}`} className="overflow-hidden">
                <div className="aspect-video bg-muted relative">
                  {item.images && item.images.length > 0 ? (
                    <img
                      src={item.images[0].url || '/placeholder.svg'}
                      alt={item.title}
                      className="w-full h-full object-cover"
                    />
                  ) : (
                    <div className="w-full h-full flex items-center justify-center">
                      <Package className="h-12 w-12 text-muted-foreground" />
                    </div>
                  )}
                  {!item.is_active && (
                    <Badge className="absolute top-2 right-2" variant="secondary">
                      Inactive
                    </Badge>
                  )}
                </div>
                <CardHeader>
                  <div className="flex items-start justify-between gap-2">
                    <CardTitle className="text-lg">{item.title}</CardTitle>
                    <Badge variant="outline">{getCategoryName(item)}</Badge>
                  </div>
                  <CardDescription className="line-clamp-2">
                    {item.description}
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Base Price:</span>
                      <span className="font-semibold">
                        ${(item.base_price / 100).toFixed(2)}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Shipping:</span>
                      <span>${(item.shipping_price_normal / 100).toFixed(2)}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Delivery:</span>
                      <span>{item.shipping_time_days} days</span>
                    </div>
                  </div>
                </CardContent>
                <CardFooter className="gap-2">
                  {hasId ? (
                    <Link href={`/auction/${item.auction_id}`} className="flex-1">
                      <Button className="w-full">View Auction Details</Button>
                    </Link>
                  ) : (
                    <Button className="w-full" disabled>
                      Missing Item ID
                    </Button>
                  )}
                </CardFooter>
              </Card>
            );
          })}
        </div>
      )}
    </div>
  );
}
