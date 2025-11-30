'use client';

import React, { useState, useEffect } from 'react';
import { api, Order, ApiError } from '@/lib/api';
import { useAuth } from '@/lib/auth-context';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { useToast } from '@/hooks/use-toast';
import { ArrowLeft, CreditCard } from 'lucide-react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';

export default function PaymentPage({ params }: { params: Promise<{ id: string }> }) {
  // Unwrap Next.js 15 async params
  const { id } = React.use(params);
  
  const { user, isLoading: authLoading } = useAuth();
  const router = useRouter();
  const { toast } = useToast();
  const [order, setOrder] = useState<Order | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isPaying, setIsPaying] = useState(false);

  const [paymentData, setPaymentData] = useState({
    card_number: '',
    card_holder_name: '',
    expiry_month: '',
    expiry_year: '',
    cvv: '',
  });

  useEffect(() => {
    if (!authLoading && !user) {
      router.push('/auth');
    }
  }, [user, authLoading, router]);

  useEffect(() => {
    if (!id) return;
    loadOrder();
  }, [id]);

  const loadOrder = async () => {
    if (!id) return;
    
    setIsLoading(true);
    try {
      const orderData = await api.getOrder(id); // Pass UUID as string
      setOrder(orderData);
    } catch (error) {
      console.error('Failed to load order:', error);
      const message = error instanceof ApiError ? error.message : 'Failed to load order';
      toast({
        title: 'Error',
        description: message,
        variant: 'destructive',
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handlePayment = async (e: React.FormEvent) => {
    e.preventDefault();

    // Validation
    if (paymentData.card_number.length < 13) {
      toast({
        title: 'Validation Error',
        description: 'Please enter a valid card number',
        variant: 'destructive',
      });
      return;
    }

    const month = parseInt(paymentData.expiry_month);
    const year = parseInt(paymentData.expiry_year);
    const currentYear = new Date().getFullYear();

    if (month < 1 || month > 12) {
      toast({
        title: 'Validation Error',
        description: 'Expiry month must be between 1 and 12',
        variant: 'destructive',
      });
      return;
    }

    if (year < currentYear) {
      toast({
        title: 'Validation Error',
        description: 'Card has expired',
        variant: 'destructive',
      });
      return;
    }

    if (paymentData.cvv.length < 3) {
      toast({
        title: 'Validation Error',
        description: 'Please enter a valid CVV',
        variant: 'destructive',
      });
      return;
    }

    if (!order) return;

    setIsPaying(true);

    try {
      await api.payOrder(order.id, {
        card_number: paymentData.card_number,
        card_holder_name: paymentData.card_holder_name,
        expiry_month: month,
        expiry_year: year,
        cvv: paymentData.cvv,
      });

      toast({
        title: 'Success',
        description: 'Payment processed successfully',
      });

      router.push(`/order/${order.id}/receipt`);
    } catch (error) {
      console.error('Payment failed:', error);
      const message = error instanceof ApiError ? error.message : 'Payment failed';
      toast({
        title: 'Payment Error',
        description: message,
        variant: 'destructive',
      });
    } finally {
      setIsPaying(false);
    }
  };

  if (authLoading || isLoading) {
    return (
      <div className="container mx-auto px-4 py-8">
        <p className="text-center text-muted-foreground">Loading...</p>
      </div>
    );
  }

  if (!order) {
    return (
      <div className="container mx-auto px-4 py-8">
        <p className="text-center text-muted-foreground">Order not found</p>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-8 max-w-2xl">
      <Link href={`/order/create?auction=${order.auction_id}`}>
        <Button variant="ghost" className="mb-6">
          <ArrowLeft className="h-4 w-4 mr-2" />
          Back
        </Button>
      </Link>

      <h1 className="text-3xl font-bold mb-8">Payment</h1>

      <div className="space-y-6">
        <Card>
          <CardHeader>
            <CardTitle>Order Total</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-3xl font-bold">
              ${order.total_amount ? (order.total_amount / 100).toFixed(2) : 'Calculating...'}
            </p>
            <p className="text-sm text-muted-foreground mt-1">
              Order #{order.id}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <CreditCard className="h-5 w-5" />
              Payment Details
            </CardTitle>
            <CardDescription>
              Enter your card information to complete the purchase
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handlePayment} className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="card_holder_name">Cardholder Name *</Label>
                <Input
                  id="card_holder_name"
                  type="text"
                  required
                  value={paymentData.card_holder_name}
                  onChange={(e) =>
                    setPaymentData({ ...paymentData, card_holder_name: e.target.value })
                  }
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="card_number">Card Number *</Label>
                <Input
                  id="card_number"
                  type="text"
                  required
                  maxLength={16}
                  placeholder="1234567890123456"
                  value={paymentData.card_number}
                  onChange={(e) =>
                    setPaymentData({ ...paymentData, card_number: e.target.value.replace(/\D/g, '') })
                  }
                />
              </div>

              <div className="grid grid-cols-3 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="expiry_month">Month *</Label>
                  <Input
                    id="expiry_month"
                    type="number"
                    min="1"
                    max="12"
                    required
                    placeholder="MM"
                    value={paymentData.expiry_month}
                    onChange={(e) =>
                      setPaymentData({ ...paymentData, expiry_month: e.target.value })
                    }
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="expiry_year">Year *</Label>
                  <Input
                    id="expiry_year"
                    type="number"
                    min={new Date().getFullYear()}
                    required
                    placeholder="YYYY"
                    value={paymentData.expiry_year}
                    onChange={(e) =>
                      setPaymentData({ ...paymentData, expiry_year: e.target.value })
                    }
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="cvv">CVV *</Label>
                  <Input
                    id="cvv"
                    type="text"
                    required
                    maxLength={4}
                    placeholder="123"
                    value={paymentData.cvv}
                    onChange={(e) =>
                      setPaymentData({ ...paymentData, cvv: e.target.value.replace(/\D/g, '') })
                    }
                  />
                </div>
              </div>

              <Button type="submit" size="lg" className="w-full" disabled={isPaying}>
                {isPaying ? 'Processing Payment...' : 'Pay Now'}
              </Button>
            </form>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
