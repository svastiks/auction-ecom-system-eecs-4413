'use client';

import type React from 'react';

import { useState, useEffect } from 'react';
import { api, type Item, type Category, ApiError } from '@/lib/api';
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

export default function CataloguePage() {
  const { user, isLoading: authLoading } = useAuth();
  const router = useRouter();
  const { toast } = useToast();
  const [items, setItems] = useState<Item[]>([]);
  const [categories, setCategories] = useState<Category[]>([]);
  const [searchKeyword, setSearchKeyword] = useState('');
  const [isLoading, setIsLoading] = useState(true);
  const [isSearching, setIsSearching] = useState(false);

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
      const [itemsData, categoriesData] = await Promise.all([
        api.getItems(),
        api.getCategories(),
      ]);
      const normalizedItems = normalizeItems(itemsData as any[]);
      setItems(normalizedItems);
      setCategories(categoriesData);
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
      const auctions = await api.searchAuctions(searchKeyword);
      // Extract and normalize items from auction results
      const searchedItems = normalizeItems(
        (auctions as any[])
          .map((auction: any) => auction.item)
          .filter(Boolean),
      );
      setItems(searchedItems);

      if (searchedItems.length === 0) {
        toast({
          title: 'No results',
          description: 'No items found matching your search',
        });
      }
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

  const getCategoryName = (categoryId: number) => {
    const category = categories.find((c) => c.id === categoryId);
    return category?.name || 'Uncategorized';
  };

  if (authLoading || isLoading) {
    return (
      <div className="container mx-auto px-4 py-8">
        <p className="text-center text-muted-foreground">Loading catalogue...</p>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold mb-4">Item Catalogue</h1>

        <form onSubmit={handleSearch} className="flex gap-2 max-w-xl">
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
      </div>

      {items.length === 0 ? (
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
          {items.map((item) => {
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
                    <Badge variant="outline">{getCategoryName(item.category_id)}</Badge>
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
