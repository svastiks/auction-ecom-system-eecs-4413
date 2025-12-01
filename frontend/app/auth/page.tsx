'use client';

import { useState } from 'react';
import { useAuth } from '@/lib/auth-context';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog';
import { useToast } from '@/hooks/use-toast';
import { ApiError, api, AddressInput } from '@/lib/api';
import { Checkbox } from '@/components/ui/checkbox';
import { MapPin } from 'lucide-react';

export default function AuthPage() {
  const { login, signup } = useAuth();
  const { toast } = useToast();
  const [isLoading, setIsLoading] = useState(false);

  // Sign In state
  const [signInData, setSignInData] = useState({
    username: '',
    password: '',
  });

  // Sign Up state
  const [signUpData, setSignUpData] = useState({
    username: '',
    email: '',
    first_name: '',
    last_name: '',
    phone: '',
    password: '',
  });

  // Address state for sign up
  const [addressData, setAddressData] = useState<AddressInput>({
    street_line1: '',
    street_line2: '',
    city: '',
    state_region: '',
    postal_code: '',
    country: '',
    is_default_shipping: true,
  });
  const [addressDialogOpen, setAddressDialogOpen] = useState(false);
  const [hasAddress, setHasAddress] = useState(false);

  // Forgot Password state
  const [forgotEmail, setForgotEmail] = useState('');
  const [resetToken, setResetToken] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [forgotStep, setForgotStep] = useState<'email' | 'reset'>('email');
  const [forgotDialogOpen, setForgotDialogOpen] = useState(false);

  const handleSignIn = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);

    try {
      await login(signInData.username, signInData.password);
      toast({
        title: 'Success',
        description: 'Logged in successfully',
      });
    } catch (error) {
      console.error('Login error:', error);
      const message = error instanceof ApiError ? error.message : 'Login failed';
      toast({
        title: 'Error',
        description: message,
        variant: 'destructive',
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleSignUp = async (e: React.FormEvent) => {
    e.preventDefault();

    // Validation
    if (signUpData.password.length < 8) {
      toast({
        title: 'Validation Error',
        description: 'Password must be at least 8 characters',
        variant: 'destructive',
      });
      return;
    }

    if (!signUpData.email.includes('@')) {
      toast({
        title: 'Validation Error',
        description: 'Please enter a valid email',
        variant: 'destructive',
      });
      return;
    }

    setIsLoading(true);

    try {
      // Combine signup data with address data
      const signupPayload = {
        ...signUpData,
        address: hasAddress ? addressData : undefined,
      };

      await signup(signupPayload);
      toast({
        title: 'Success',
        description: 'Account created successfully',
      });
    } catch (error) {
      console.error('Signup error:', error);
      const message = error instanceof ApiError ? error.message : 'Signup failed';
      toast({
        title: 'Error',
        description: message,
        variant: 'destructive',
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleAddressSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    e.stopPropagation(); // Prevent triggering parent form submission

    if (!addressData.street_line1 || !addressData.city || !addressData.state_region ||
        !addressData.postal_code || !addressData.country) {
      toast({
        title: 'Validation Error',
        description: 'Please fill in all required address fields',
        variant: 'destructive',
      });
      return;
    }

    setHasAddress(true);
    setAddressDialogOpen(false);
    toast({
      title: 'Address Added',
      description: 'Address will be saved when you create your account',
    });
  };

  const resetAddressForm = () => {
    setAddressData({
      street_line1: '',
      street_line2: '',
      city: '',
      state_region: '',
      postal_code: '',
      country: '',
      is_default_shipping: true,
    });
    setHasAddress(false);
  };

  const handleForgotPassword = async () => {
    setIsLoading(true);
    try {
      const response = await api.forgotPassword(forgotEmail);

      // Check if email was verified (token was generated)
      const message = (response as any).message || '';

      if (message.includes('Password reset token:')) {
        // Extract token from the message
        const token = message.replace('Password reset token:', '').trim();

        // Log to console
        console.log(`Email verified. Reset token is: ${token}`);

        // Show success toast
        toast({
          title: 'Token sent',
          description: 'Check console for reset token',
        });

        // Move to reset step
        setForgotStep('reset');
      } else {
        // Email not found in database
        toast({
          title: 'Email not verified. Try Again.',
          variant: 'destructive',
        });
      }
    } catch (error) {
      console.error('Forgot password error:', error);
      toast({
        title: 'Email not verified. Try Again.',
        variant: 'destructive',
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleResetPassword = async () => {
    if (newPassword.length < 8) {
      toast({
        title: 'Validation Error',
        description: 'Password must be at least 8 characters',
        variant: 'destructive',
      });
      return;
    }

    setIsLoading(true);
    try {
      await api.resetPassword(resetToken, newPassword);
      toast({
        title: 'Success',
        description: 'Password reset successfully',
      });
      setForgotDialogOpen(false);
      setForgotStep('email');
      setResetToken('');
      setNewPassword('');
      setForgotEmail('');
    } catch (error) {
      const message = error instanceof ApiError ? error.message : 'Failed to reset password';
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
    <div className="min-h-screen flex items-center justify-center bg-muted/30 p-4">
      <Card className="w-full max-w-md">
        <CardHeader>
          <CardTitle className="text-2xl">AuctionHub</CardTitle>
          <CardDescription>Sign in to your account or create a new one</CardDescription>
        </CardHeader>
        <CardContent>
          <Tabs defaultValue="signin" className="w-full">
            <TabsList className="grid w-full grid-cols-2">
              <TabsTrigger value="signin">Sign In</TabsTrigger>
              <TabsTrigger value="signup">Sign Up</TabsTrigger>
            </TabsList>

            <TabsContent value="signin">
              <form onSubmit={handleSignIn} className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="signin-username">Username</Label>
                  <Input
                    id="signin-username"
                    type="text"
                    required
                    value={signInData.username}
                    onChange={(e) =>
                      setSignInData({ ...signInData, username: e.target.value })
                    }
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="signin-password">Password</Label>
                  <Input
                    id="signin-password"
                    type="password"
                    required
                    value={signInData.password}
                    onChange={(e) =>
                      setSignInData({ ...signInData, password: e.target.value })
                    }
                  />
                </div>
                <Button type="submit" className="w-full" disabled={isLoading}>
                  {isLoading ? 'Signing in...' : 'Sign In'}
                </Button>

                <Dialog open={forgotDialogOpen} onOpenChange={setForgotDialogOpen}>
                  <DialogTrigger asChild>
                    <Button variant="link" className="w-full" type="button">
                      Forgot password?
                    </Button>
                  </DialogTrigger>
                  <DialogContent>
                    <DialogHeader>
                      <DialogTitle>Reset Password</DialogTitle>
                      <DialogDescription>
                        {forgotStep === 'email'
                          ? 'Enter your email to receive a reset token'
                          : 'Enter the token from your email and your new password'}
                      </DialogDescription>
                    </DialogHeader>
                    {forgotStep === 'email' ? (
                      <div className="space-y-4">
                        <div className="space-y-2">
                          <Label htmlFor="forgot-email">Email</Label>
                          <Input
                            id="forgot-email"
                            type="email"
                            value={forgotEmail}
                            onChange={(e) => setForgotEmail(e.target.value)}
                          />
                        </div>
                        <Button onClick={handleForgotPassword} disabled={isLoading} className="w-full">
                          Send Reset Token
                        </Button>
                      </div>
                    ) : (
                      <div className="space-y-4">
                        <div className="space-y-2">
                          <Label htmlFor="reset-token">Reset Token</Label>
                          <Input
                            id="reset-token"
                            type="text"
                            value={resetToken}
                            onChange={(e) => setResetToken(e.target.value)}
                          />
                        </div>
                        <div className="space-y-2">
                          <Label htmlFor="new-password">New Password</Label>
                          <Input
                            id="new-password"
                            type="password"
                            value={newPassword}
                            onChange={(e) => setNewPassword(e.target.value)}
                          />
                        </div>
                        <Button onClick={handleResetPassword} disabled={isLoading} className="w-full">
                          Reset Password
                        </Button>
                      </div>
                    )}
                  </DialogContent>
                </Dialog>
              </form>
            </TabsContent>

            <TabsContent value="signup">
              <form onSubmit={handleSignUp} className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="first-name">First Name</Label>
                    <Input
                      id="first-name"
                      type="text"
                      required
                      value={signUpData.first_name}
                      onChange={(e) =>
                        setSignUpData({ ...signUpData, first_name: e.target.value })
                      }
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="last-name">Last Name</Label>
                    <Input
                      id="last-name"
                      type="text"
                      required
                      value={signUpData.last_name}
                      onChange={(e) =>
                        setSignUpData({ ...signUpData, last_name: e.target.value })
                      }
                    />
                  </div>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="username">Username</Label>
                  <Input
                    id="username"
                    type="text"
                    required
                    value={signUpData.username}
                    onChange={(e) =>
                      setSignUpData({ ...signUpData, username: e.target.value })
                    }
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="email">Email</Label>
                  <Input
                    id="email"
                    type="email"
                    required
                    value={signUpData.email}
                    onChange={(e) =>
                      setSignUpData({ ...signUpData, email: e.target.value })
                    }
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="phone">Phone</Label>
                  <Input
                    id="phone"
                    type="tel"
                    required
                    value={signUpData.phone}
                    onChange={(e) =>
                      setSignUpData({ ...signUpData, phone: e.target.value })
                    }
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="password">Password</Label>
                  <Input
                    id="password"
                    type="password"
                    required
                    minLength={8}
                    value={signUpData.password}
                    onChange={(e) =>
                      setSignUpData({ ...signUpData, password: e.target.value })
                    }
                  />
                  <p className="text-xs text-muted-foreground">
                    Must be at least 8 characters
                  </p>
                </div>

                <div className="space-y-2">
                  <Label>Shipping Address (Optional)</Label>
                  {hasAddress ? (
                    <div className="p-3 rounded-lg border bg-muted/50">
                      <div className="flex items-start justify-between">
                        <div className="space-y-1">
                          <div className="flex items-center gap-2">
                            <MapPin className="h-4 w-4 text-muted-foreground" />
                            <p className="text-sm font-medium">{addressData.street_line1}</p>
                          </div>
                          {addressData.street_line2 && (
                            <p className="text-xs text-muted-foreground pl-6">
                              {addressData.street_line2}
                            </p>
                          )}
                          <p className="text-xs text-muted-foreground pl-6">
                            {addressData.city}, {addressData.state_region} {addressData.postal_code}
                          </p>
                          <p className="text-xs text-muted-foreground pl-6">
                            {addressData.country}
                          </p>
                        </div>
                        <Button
                          type="button"
                          variant="ghost"
                          size="sm"
                          onClick={() => setAddressDialogOpen(true)}
                        >
                          Edit
                        </Button>
                      </div>
                    </div>
                  ) : (
                    <Button type="button" variant="outline" className="w-full" onClick={() => setAddressDialogOpen(true)}>
                      Add Shipping Address
                    </Button>
                  )}
                </div>

                <Button type="submit" className="w-full" disabled={isLoading}>
                  {isLoading ? 'Creating account...' : 'Create Account'}
                </Button>
              </form>
            </TabsContent>
          </Tabs>
        </CardContent>
      </Card>

      {/* Address Dialog - Outside form to prevent event bubbling */}
      <Dialog open={addressDialogOpen} onOpenChange={setAddressDialogOpen}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>Add Shipping Address</DialogTitle>
            <DialogDescription>
              Add a shipping address to your account (optional)
            </DialogDescription>
          </DialogHeader>
          <form onSubmit={handleAddressSubmit} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="street_line1">Street Address *</Label>
              <Input
                id="street_line1"
                required
                value={addressData.street_line1}
                onChange={(e) =>
                  setAddressData({ ...addressData, street_line1: e.target.value })
                }
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="street_line2">
                Apartment, suite, etc. (optional)
              </Label>
              <Input
                id="street_line2"
                value={addressData.street_line2}
                onChange={(e) =>
                  setAddressData({ ...addressData, street_line2: e.target.value })
                }
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="city">City *</Label>
                <Input
                  id="city"
                  required
                  value={addressData.city}
                  onChange={(e) =>
                    setAddressData({ ...addressData, city: e.target.value })
                  }
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="state_region">State/Region *</Label>
                <Input
                  id="state_region"
                  required
                  value={addressData.state_region}
                  onChange={(e) =>
                    setAddressData({ ...addressData, state_region: e.target.value })
                  }
                />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="postal_code">Postal Code *</Label>
                <Input
                  id="postal_code"
                  required
                  value={addressData.postal_code}
                  onChange={(e) =>
                    setAddressData({ ...addressData, postal_code: e.target.value })
                  }
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="country">Country *</Label>
                <Input
                  id="country"
                  required
                  value={addressData.country}
                  onChange={(e) =>
                    setAddressData({ ...addressData, country: e.target.value })
                  }
                />
              </div>
            </div>

            <div className="flex items-center space-x-2">
              <Checkbox
                id="is_default"
                checked={addressData.is_default_shipping}
                onCheckedChange={(checked) =>
                  setAddressData({
                    ...addressData,
                    is_default_shipping: checked as boolean,
                  })
                }
              />
              <Label htmlFor="is_default" className="cursor-pointer">
                Set as default shipping address
              </Label>
            </div>

            <div className="flex gap-3 pt-4">
              <Button type="submit" className="flex-1">
                Add Address
              </Button>
              <Button
                type="button"
                variant="outline"
                onClick={() => {
                  setAddressDialogOpen(false);
                }}
                className="flex-1"
              >
                Cancel
              </Button>
            </div>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
}
