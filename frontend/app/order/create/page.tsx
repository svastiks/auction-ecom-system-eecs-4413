'use client';

import { useState, useEffect } from 'react';
import { api, Auction, Address, ApiError } from '@/lib/api';
import { useAuth } from '@/lib/auth-context';
import { Button } from '@/components/ui/button';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group';
import { useToast } from '@/hooks/use-toast';
import { ArrowLeft, Truck } from 'lucide-react';
import Link from 'next/link';
import { useRouter, useSearchParams } from 'next/navigation';

export default function CreateOrderPage() {
  const { user, isLoading: authLoading } = useAuth();
  const router = useRouter();
  const searchParams = useSearchParams();
  const { toast } = useToast();
  
  const auctionId = searchParams.get('auction');
  const [auction, setAuction] = useState<Auction | null>(null);
  const [addresses, setAddresses] = useState<Address[]>([]);
  const [selectedAddressId, setSelectedAddressId] = useState<string>('');
  const [shippingMethod, setShippingMethod] = useState<'NORMAL' | 'EXPEDITED'>('NORMAL');
  const [isLoading, setIsLoading] = useState(true);
  const [isCreating, setIsCreating] = useState(false);

  useEffect(() => {
    if (!authLoading && !user) {
      router.push('/auth');
    }
  }, [user, authLoading, router]);

  useEffect(() => {
    if (!auctionId) {
      toast({
        title: 'Error',
        description: 'No auction specified',
        variant: 'destructive',
      });
      router.push('/catalogue');
      return;
    }
    loadData();
  }, [auctionId]);

  const loadData = async () => {
    if (!auctionId) return;
    
    setIsLoading(true);
    try {
      const [auctionData, addressesData] = await Promise.all([
        api.getAuction(Number(auctionId)),
        api.getAddresses(),
      ]);
      
      setAuction(auctionData);
      setAddresses(addressesData);
      
      // Auto-select default shipping address
      const defaultAddress = addressesData.find(addr => addr.is_default_shipping);
      if (defaultAddress) {
        setSelectedAddressId(String(defaultAddress.id));
      } else if (addressesData.length > 0) {
        setSelectedAddressId(String(addressesData[0].id));
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

  const handleCreateOrder = async () => {
    if (!selectedAddressId) {
      toast({
        title: 'Error',
        description: 'Please select a shipping address',
        variant: 'destructive',
      });
      return;
    }

    if (!auction) return;

    setIsCreating(true);

    try {
      const order = await api.createOrder({
        shipping_method: shippingMethod,
        shipping_address_id: Number(selectedAddressId),
        auction_id: auction.id,
      });
      
      toast({
        title: 'Success',
        description: 'Order created successfully',
      });
      
      router.push(`/order/${order.id}/payment`);
    } catch (error) {
      console.error('[v0] Failed to create order:', error);
      const message = error instanceof ApiError ? error.message : 'Failed to create order';
      toast({
        title: 'Error',
        description: message,
        variant: 'destructive',
      });
    } finally {
      setIsCreating(false);
    }
  };

  if (authLoading || isLoading) {
    return (
      <div className="container mx-auto px-4 py-8">
        <p className="text-center text-muted-foreground">Loading...</p>
      </div>
    );
  }

  if (!auction || !auction.item) {
    return (
      <div className="container mx-auto px-4 py-8">
        <p className="text-center text-muted-foreground">Auction not found</p>
      </div>
    );
  }

  const winningBid = auction.current_highest_bid || auction.starting_price;
  const shippingCost = shippingMethod === 'NORMAL' 
    ? auction.item.shipping_price_normal 
    : auction.item.shipping_price_expedited;
  const totalAmount = winningBid + shippingCost;

  return (
    <div className="container mx-auto px-4 py-8 max-w-3xl">
      <Link href={`/auction/${auction.id}`}>
        <Button variant="ghost" className="mb-6">
          <ArrowLeft className="h-4 w-4 mr-2" />
          Back to Auction
        </Button>
      </Link>

      <h1 className="text-3xl font-bold mb-8">Complete Your Order</h1>

      <div className="space-y-6">
        {/* Order Summary */}
        <Card>
          <CardHeader>
            <CardTitle>Order Summary</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center gap-4">
              {auction.item.images && auction.item.images.length > 0 && (
                <img
                  src={auction.item.images[0].url || "/placeholder.svg"}
                  alt={auction.item.title}
                  className="w-20 h-20 object-cover rounded"
                />
              )}
              <div>
                <h3 className="font-semibold">{auction.item.title}</h3>
                <p className="text-sm text-muted-foreground">Auction #{auction.id}</p>
              </div>
            </div>
            
            <div className="border-t pt-4 space-y-2">
              <div className="flex justify-between text-sm">
                <span className="text-muted-foreground">Winning Bid:</span>
                <span className="font-medium">${(winningBid / 100).toFixed(2)}</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-muted-foreground">Shipping ({shippingMethod}):</span>
                <span className="font-medium">${(shippingCost / 100).toFixed(2)}</span>
              </div>
              <div className="flex justify-between text-lg font-bold border-t pt-2">
                <span>Total:</span>
                <span>${(totalAmount / 100).toFixed(2)}</span>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Shipping Method */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Truck className="h-5 w-5" />
              Shipping Method
            </CardTitle>
            <CardDescription>
              Estimated delivery: {auction.item.shipping_time_days} days
            </CardDescription>
          </CardHeader>
          <CardContent>
            <RadioGroup value={shippingMethod} onValueChange={(value: any) => setShippingMethod(value)}>
              <div className="flex items-center space-x-2 p-3 rounded-lg border">
                <RadioGroupItem value="NORMAL" id="normal" />
                <Label htmlFor="normal" className="flex-1 cursor-pointer">
                  <div className="flex justify-between">
                    <span>Normal Shipping</span>
                    <span className="font-semibold">
                      ${(auction.item.shipping_price_normal / 100).toFixed(2)}
                    </span>
                  </div>
                </Label>
              </div>
              <div className="flex items-center space-x-2 p-3 rounded-lg border">
                <RadioGroupItem value="EXPEDITED" id="expedited" />
                <Label htmlFor="expedited" className="flex-1 cursor-pointer">
                  <div className="flex justify-between">
                    <span>Expedited Shipping</span>
                    <span className="font-semibold">
                      ${(auction.item.shipping_price_expedited / 100).toFixed(2)}
                    </span>
                  </div>
                </Label>
              </div>
            </RadioGroup>
          </CardContent>
        </Card>

        {/* Shipping Address */}
        <Card>
          <CardHeader>
            <CardTitle>Shipping Address</CardTitle>
          </CardHeader>
          <CardContent>
            {addresses.length === 0 ? (
              <div className="text-center py-4">
                <p className="text-muted-foreground mb-4">No addresses found</p>
                <Link href="/account">
                  <Button>Add Address</Button>
                </Link>
              </div>
            ) : (
              <RadioGroup value={selectedAddressId} onValueChange={setSelectedAddressId}>
                {addresses.map((address) => (
                  <div key={address.id} className="flex items-start space-x-2 p-3 rounded-lg border">
                    <RadioGroupItem value={String(address.id)} id={`addr-${address.id}`} className="mt-1" />
                    <Label htmlFor={`addr-${address.id}`} className="flex-1 cursor-pointer">
                      <div className="space-y-1">
                        <p className="font-medium">
                          {address.street_line1}
                          {address.is_default_shipping && (
                            <span className="ml-2 text-xs text-primary">(Default)</span>
                          )}
                        </p>
                        {address.street_line2 && (
                          <p className="text-sm text-muted-foreground">{address.street_line2}</p>
                        )}
                        <p className="text-sm text-muted-foreground">
                          {address.city}, {address.state_region} {address.postal_code}
                        </p>
                        <p className="text-sm text-muted-foreground">{address.country}</p>
                      </div>
                    </Label>
                  </div>
                ))}
              </RadioGroup>
            )}
          </CardContent>
        </Card>

        <Button 
          onClick={handleCreateOrder} 
          size="lg" 
          className="w-full"
          disabled={isCreating || addresses.length === 0}
        >
          {isCreating ? 'Processing...' : 'Proceed to Payment'}
        </Button>
      </div>
    </div>
  );
}
