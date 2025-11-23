'use client';

import { useState, useEffect } from 'react';
import { api, Item, AuctionInput, ApiError } from '@/lib/api';
import { useAuth } from '@/lib/auth-context';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { useToast } from '@/hooks/use-toast';
import { useRouter } from 'next/navigation';
import { ArrowLeft } from 'lucide-react';
import Link from 'next/link';

export default function CreateAuctionPage() {
  const { user, isLoading: authLoading } = useAuth();
  const router = useRouter();
  const { toast } = useToast();
  const [items, setItems] = useState<Item[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  const [formData, setFormData] = useState({
    item_id: '',
    starting_price: '',
    min_increment: '1',
    start_time: '',
    end_time: '',
  });

  useEffect(() => {
    if (!authLoading && !user) {
      router.push('/auth');
    }
  }, [user, authLoading, router]);

  useEffect(() => {
    loadItems();
    // Set default times
    const now = new Date();
    const start = new Date(now.getTime() + 5 * 60000); // 5 minutes from now
    const end = new Date(now.getTime() + 7 * 24 * 60 * 60000); // 7 days from now
    
    setFormData(prev => ({
      ...prev,
      start_time: start.toISOString().slice(0, 16),
      end_time: end.toISOString().slice(0, 16),
    }));
  }, []);

  const loadItems = async () => {
    try {
      const itemsData = await api.getItems();
      setItems(itemsData.filter(item => item.is_active));
    } catch (error) {
      console.error('[v0] Failed to load items:', error);
      toast({
        title: 'Error',
        description: 'Failed to load items',
        variant: 'destructive',
      });
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!formData.item_id) {
      toast({
        title: 'Validation Error',
        description: 'Please select an item',
        variant: 'destructive',
      });
      return;
    }

    const selectedItem = items.find(item => item.id === Number(formData.item_id));
    const starting_price = Math.round(parseFloat(formData.starting_price) * 100);
    const min_increment = Math.round(parseFloat(formData.min_increment) * 100);

    if (isNaN(starting_price) || starting_price <= 0) {
      toast({
        title: 'Validation Error',
        description: 'Starting price must be a valid positive number',
        variant: 'destructive',
      });
      return;
    }

    if (selectedItem && starting_price < selectedItem.base_price) {
      toast({
        title: 'Validation Error',
        description: 'Starting price must be at least the base price',
        variant: 'destructive',
      });
      return;
    }

    if (min_increment < 100) {
      toast({
        title: 'Validation Error',
        description: 'Minimum increment must be at least $1',
        variant: 'destructive',
      });
      return;
    }

    const startTime = new Date(formData.start_time);
    const endTime = new Date(formData.end_time);

    if (startTime >= endTime) {
      toast({
        title: 'Validation Error',
        description: 'End time must be after start time',
        variant: 'destructive',
      });
      return;
    }

    if (endTime <= new Date()) {
      toast({
        title: 'Validation Error',
        description: 'End time must be in the future',
        variant: 'destructive',
      });
      return;
    }

    setIsLoading(true);

    try {
      const auctionInput: AuctionInput = {
        auction_type: 'FORWARD',
        starting_price,
        min_increment,
        start_time: startTime.toISOString(),
        end_time: endTime.toISOString(),
        status: 'ACTIVE',
        item_id: Number(formData.item_id),
      };

      const createdAuction = await api.createAuction(auctionInput);
      
      toast({
        title: 'Success',
        description: 'Auction created successfully',
      });
      
      router.push(`/auction/${createdAuction.id}`);
    } catch (error) {
      console.error('[v0] Failed to create auction:', error);
      const message = error instanceof ApiError ? error.message : 'Failed to create auction';
      toast({
        title: 'Error',
        description: message,
        variant: 'destructive',
      });
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="container mx-auto px-4 py-8 max-w-2xl">
      <Link href="/catalogue">
        <Button variant="ghost" className="mb-6">
          <ArrowLeft className="h-4 w-4 mr-2" />
          Back to Catalogue
        </Button>
      </Link>

      <Card>
        <CardHeader>
          <CardTitle>Create New Auction</CardTitle>
          <CardDescription>
            Create a forward auction for an existing catalogue item
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-6">
            <div className="space-y-2">
              <Label htmlFor="item">Select Item *</Label>
              <Select
                value={formData.item_id}
                onValueChange={(value) => {
                  const item = items.find(i => i.id === Number(value));
                  setFormData({ 
                    ...formData, 
                    item_id: value,
                    starting_price: item ? (item.base_price / 100).toFixed(2) : '',
                  });
                }}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Select an item to auction" />
                </SelectTrigger>
                <SelectContent>
                  {items.map((item) => (
                    <SelectItem key={item.id} value={String(item.id)}>
                      {item.title} (Base: ${(item.base_price / 100).toFixed(2)})
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              {items.length === 0 && (
                <p className="text-sm text-muted-foreground">
                  No active items available.{' '}
                  <Link href="/seller/create-item" className="text-primary hover:underline">
                    Create an item first
                  </Link>
                </p>
              )}
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="starting_price">Starting Price ($) *</Label>
                <Input
                  id="starting_price"
                  type="number"
                  step="0.01"
                  min="0"
                  required
                  value={formData.starting_price}
                  onChange={(e) => setFormData({ ...formData, starting_price: e.target.value })}
                />
                <p className="text-xs text-muted-foreground">
                  Must be at least the item's base price
                </p>
              </div>

              <div className="space-y-2">
                <Label htmlFor="min_increment">Min Increment ($) *</Label>
                <Input
                  id="min_increment"
                  type="number"
                  step="0.01"
                  min="1"
                  required
                  value={formData.min_increment}
                  onChange={(e) => setFormData({ ...formData, min_increment: e.target.value })}
                />
                <p className="text-xs text-muted-foreground">
                  Minimum bid increment
                </p>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="start_time">Start Time *</Label>
                <Input
                  id="start_time"
                  type="datetime-local"
                  required
                  value={formData.start_time}
                  onChange={(e) => setFormData({ ...formData, start_time: e.target.value })}
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="end_time">End Time *</Label>
                <Input
                  id="end_time"
                  type="datetime-local"
                  required
                  value={formData.end_time}
                  onChange={(e) => setFormData({ ...formData, end_time: e.target.value })}
                />
              </div>
            </div>

            <div className="flex gap-3">
              <Button type="submit" disabled={isLoading || items.length === 0} className="flex-1">
                {isLoading ? 'Creating...' : 'Create Auction'}
              </Button>
              <Link href="/catalogue" className="flex-1">
                <Button type="button" variant="outline" className="w-full">
                  Cancel
                </Button>
              </Link>
            </div>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
