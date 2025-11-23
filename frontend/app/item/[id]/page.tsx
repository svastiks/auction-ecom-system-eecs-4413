'use client';

import { useState, useEffect } from 'react';
import { api, Item, ApiError } from '@/lib/api';
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
import { Package, ArrowLeft } from 'lucide-react';
import Link from 'next/link';
import { useRouter, useParams } from 'next/navigation';

export default function ItemDetailPage() {
  const { user, isLoading: authLoading } = useAuth();
  const router = useRouter();
  const { toast } = useToast();
  const params = useParams<{ id: string }>();
  const id = params?.id;

  const [item, setItem] = useState<Item | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [currentImageIndex, setCurrentImageIndex] = useState(0);

  useEffect(() => {
    // redirect to /auth if user not logged in once auth check is done
    if (!authLoading && !user) {
      router.push('/auth');
    }
  }, [user, authLoading, router]);

  useEffect(() => {
    if (!id) return;
    loadItem(id);
  }, [id]);

  const loadItem = async (itemId: string) => {
    setIsLoading(true);
    try {
      const itemData = await api.getItem(Number(itemId));
      setItem(itemData);
    } catch (error) {
      console.error('[v0] Failed to load item:', error);
      const message =
        error instanceof ApiError ? error.message : 'Failed to load item';
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
        <p className="text-center text-muted-foreground">Loading item...</p>
      </div>
    );
  }

  if (!item) {
    return (
      <div className="container mx-auto px-4 py-8">
        <p className="text-center text-muted-foreground">Item not found</p>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-8">
      <Link href="/catalogue">
        <Button variant="ghost" className="mb-6">
          <ArrowLeft className="h-4 w-4 mr-2" />
          Back to Catalogue
        </Button>
      </Link>

      <div className="grid lg:grid-cols-2 gap-8">
        {/* Images */}
        <div className="space-y-4">
          <div className="aspect-square bg-muted rounded-lg overflow-hidden">
            {item.images && item.images.length > 0 ? (
              <img
                src={item.images[currentImageIndex].url || '/placeholder.svg'}
                alt={item.title}
                className="w-full h-full object-cover"
              />
            ) : (
              <div className="w-full h-full flex items-center justify-center">
                <Package className="h-24 w-24 text-muted-foreground" />
              </div>
            )}
          </div>
          {item.images && item.images.length > 1 && (
            <div className="flex gap-2 overflow-x-auto">
              {item.images.map((image, index) => (
                <button
                  key={image.id ?? index}
                  onClick={() => setCurrentImageIndex(index)}
                  className={`flex-shrink-0 w-20 h-20 rounded-lg overflow-hidden border-2 ${
                    currentImageIndex === index
                      ? 'border-primary'
                      : 'border-border'
                  }`}
                >
                  <img
                    src={image.url || '/placeholder.svg'}
                    alt={`${item.title} ${index + 1}`}
                    className="w-full h-full object-cover"
                  />
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Details */}
        <div className="space-y-6">
          <div>
            <div className="flex items-start justify-between mb-2">
              <h1 className="text-3xl font-bold">{item.title}</h1>
              {!item.is_active && (
                <Badge variant="secondary">Inactive</Badge>
              )}
            </div>
            {item.category && (
              <Badge variant="outline" className="mb-4">
                {item.category.name}
              </Badge>
            )}
            <p className="text-muted-foreground">{item.description}</p>
          </div>

          <Card>
            <CardHeader>
              <CardTitle>Pricing & Shipping</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="flex justify-between text-sm">
                <span className="text-muted-foreground">Base Price:</span>
                <span className="font-semibold text-lg">
                  ${(item.base_price / 100).toFixed(2)}
                </span>
              </div>
              <div className="border-t pt-3 space-y-2">
                <div className="flex justify-between text-sm">
                  <span className="text-muted-foreground">
                    Normal Shipping:
                  </span>
                  <span>${(item.shipping_price_normal / 100).toFixed(2)}</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-muted-foreground">
                    Expedited Shipping:
                  </span>
                  <span>
                    ${(item.shipping_price_expedited / 100).toFixed(2)}
                  </span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-muted-foreground">
                    Estimated Delivery:
                  </span>
                  <span>{item.shipping_time_days} days</span>
                </div>
              </div>
            </CardContent>
          </Card>

          {item.keywords && (
            <Card>
              <CardHeader>
                <CardTitle>Keywords</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-muted-foreground">{item.keywords}</p>
              </CardContent>
            </Card>
          )}

          <Link href={`/auction/item/${item.id}`}>
            <Button size="lg" className="w-full">
              View Active Auctions
            </Button>
          </Link>
        </div>
      </div>
    </div>
  );
}