'use client';

import { useState, useEffect } from 'react';
import { api, Order, Auction, Shipment, ApiError } from '@/lib/api';
import { useAuth } from '@/lib/auth-context';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { useToast } from '@/hooks/use-toast';
import { CheckCircle2, Package, Truck } from 'lucide-react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';

export default function ReceiptPage({ params }: { params: { id: string } }) {
  const { user, isLoading: authLoading } = useAuth();
  const router = useRouter();
  const { toast } = useToast();
  const [order, setOrder] = useState<Order | null>(null);
  const [auction, setAuction] = useState<Auction | null>(null);
  const [shipment, setShipment] = useState<Shipment | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    if (!authLoading && !user) {
      router.push('/auth');
    }
  }, [user, authLoading, router]);

  useEffect(() => {
    loadData();
  }, [params.id]);

  const loadData = async () => {
    setIsLoading(true);
    try {
      const orderData = await api.getOrder(Number(params.id));
      setOrder(orderData);

      const auctionData = await api.getAuction(orderData.auction_id);
      setAuction(auctionData);

      try {
        const shipmentData = await api.getShipment(orderData.id);
        setShipment(shipmentData);
      } catch (error) {
        console.log('[v0] Shipment not yet available');
      }
    } catch (error) {
      console.error('[v0] Failed to load data:', error);
      const message = error instanceof ApiError ? error.message : 'Failed to load data';
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

  if (!order || !auction || !auction.item) {
    return (
      <div className="container mx-auto px-4 py-8">
        <p className="text-center text-muted-foreground">Receipt not found</p>
      </div>
    );
  }

  const winningBid = auction.current_highest_bid || auction.starting_price;
  const shippingCost = order.shipping_method === 'NORMAL'
    ? auction.item.shipping_price_normal
    : auction.item.shipping_price_expedited;
  const totalPaid = order.total_amount || (winningBid + shippingCost);

  return (
    <div className="container mx-auto px-4 py-8 max-w-3xl">
      <div className="text-center mb-8">
        <CheckCircle2 className="h-16 w-16 text-primary mx-auto mb-4" />
        <h1 className="text-3xl font-bold mb-2">Payment Successful!</h1>
        <p className="text-muted-foreground">Thank you for your purchase</p>
      </div>

      <div className="space-y-6">
        {/* Receipt */}
        <Card>
          <CardHeader>
            <CardTitle>Receipt</CardTitle>
            <CardDescription>Order #{order.id}</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center gap-4 pb-4 border-b">
              {auction.item.images && auction.item.images.length > 0 && (
                <img
                  src={auction.item.images[0].url || "/placeholder.svg"}
                  alt={auction.item.title}
                  className="w-20 h-20 object-cover rounded"
                />
              )}
              <div>
                <h3 className="font-semibold">{auction.item.title}</h3>
                <p className="text-sm text-muted-foreground">
                  Auction #{auction.id}
                </p>
              </div>
            </div>

            <div className="space-y-2">
              <div className="flex justify-between text-sm">
                <span className="text-muted-foreground">Winning Bid:</span>
                <span>${(winningBid / 100).toFixed(2)}</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-muted-foreground">
                  Shipping ({order.shipping_method}):
                </span>
                <span>${(shippingCost / 100).toFixed(2)}</span>
              </div>
              <div className="flex justify-between text-lg font-bold border-t pt-2">
                <span>Total Paid:</span>
                <span>${(totalPaid / 100).toFixed(2)}</span>
              </div>
            </div>

            <div className="pt-4 border-t">
              <div className="flex items-center justify-between">
                <span className="text-sm text-muted-foreground">Order Status:</span>
                <Badge>{order.status}</Badge>
              </div>
              <p className="text-xs text-muted-foreground mt-2">
                Order placed on {new Date(order.created_at).toLocaleString()}
              </p>
            </div>
          </CardContent>
        </Card>

        {/* Shipment */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Truck className="h-5 w-5" />
              Shipment Information
            </CardTitle>
          </CardHeader>
          <CardContent>
            {shipment ? (
              <div className="space-y-3">
                <div className="flex items-center gap-2">
                  <Package className="h-4 w-4 text-muted-foreground" />
                  <p className="text-sm">
                    The item will be shipped in{' '}
                    <span className="font-semibold">
                      {shipment.estimated_delivery_days || auction.item.shipping_time_days} days
                    </span>
                  </p>
                </div>
                {shipment.shipped_at && (
                  <p className="text-sm text-muted-foreground">
                    Shipped on: {new Date(shipment.shipped_at).toLocaleString()}
                  </p>
                )}
              </div>
            ) : (
              <p className="text-sm text-muted-foreground">
                Your item will be shipped within{' '}
                <span className="font-semibold">{auction.item.shipping_time_days} days</span>
              </p>
            )}
          </CardContent>
        </Card>

        <div className="flex gap-3">
          <Link href="/my-orders" className="flex-1">
            <Button variant="outline" className="w-full">
              View My Orders
            </Button>
          </Link>
          <Link href="/catalogue" className="flex-1">
            <Button className="w-full">
              Continue Shopping
            </Button>
          </Link>
        </div>
      </div>
    </div>
  );
}
