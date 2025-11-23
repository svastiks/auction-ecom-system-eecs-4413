'use client';

import { useState, useEffect } from 'react';
import { api, Address, AddressInput, ApiError } from '@/lib/api';
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
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog';
import { useToast } from '@/hooks/use-toast';
import { MapPin, Edit2, Trash2, Plus } from 'lucide-react';
import { useRouter } from 'next/navigation';
import { Checkbox } from '@/components/ui/checkbox';

export default function AccountPage() {
  const { user, isLoading: authLoading, refreshUser } = useAuth();
  const router = useRouter();
  const { toast } = useToast();
  const [addresses, setAddresses] = useState<Address[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [addressDialogOpen, setAddressDialogOpen] = useState(false);
  const [editingAddress, setEditingAddress] = useState<Address | null>(null);
  const [deleteAddressId, setDeleteAddressId] = useState<number | null>(null);

  const [profileData, setProfileData] = useState({
    first_name: '',
    last_name: '',
    email: '',
    phone: '',
  });

  const [addressData, setAddressData] = useState<AddressInput>({
    street_line1: '',
    street_line2: '',
    city: '',
    state_region: '',
    postal_code: '',
    country: '',
    is_default_shipping: false,
  });

  useEffect(() => {
    if (!authLoading && !user) {
      router.push('/auth');
    }
  }, [user, authLoading, router]);

  useEffect(() => {
    if (user) {
      setProfileData({
        first_name: user.first_name || '',
        last_name: user.last_name || '',
        email: user.email || '',
        phone: user.phone || '',
      });
      loadAddresses();
    }
  }, [user]);

  const loadAddresses = async () => {
    setIsLoading(true);
    try {
      const addressesData = await api.getAddresses();
      setAddresses(addressesData);
    } catch (error) {
      console.error('[v0] Failed to load addresses:', error);
      const message = error instanceof ApiError ? error.message : 'Failed to load addresses';
      toast({
        title: 'Error',
        description: message,
        variant: 'destructive',
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleUpdateProfile = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!profileData.email.includes('@')) {
      toast({
        title: 'Validation Error',
        description: 'Please enter a valid email',
        variant: 'destructive',
      });
      return;
    }

    setIsSaving(true);

    try {
      await api.updateMe(profileData);
      await refreshUser();

      toast({
        title: 'Success',
        description: 'Profile updated successfully',
      });
    } catch (error) {
      console.error('[v0] Failed to update profile:', error);
      const message = error instanceof ApiError ? error.message : 'Failed to update profile';
      toast({
        title: 'Error',
        description: message,
        variant: 'destructive',
      });
    } finally {
      setIsSaving(false);
    }
  };

  const handleAddressSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!addressData.street_line1 || !addressData.city || !addressData.state_region || 
        !addressData.postal_code || !addressData.country) {
      toast({
        title: 'Validation Error',
        description: 'Please fill in all required address fields',
        variant: 'destructive',
      });
      return;
    }

    setIsSaving(true);

    try {
      if (editingAddress) {
        await api.updateAddress(editingAddress.id, addressData);
        toast({
          title: 'Success',
          description: 'Address updated successfully',
        });
      } else {
        await api.createAddress(addressData);
        toast({
          title: 'Success',
          description: 'Address added successfully',
        });
      }

      await loadAddresses();
      setAddressDialogOpen(false);
      resetAddressForm();
    } catch (error) {
      console.error('[v0] Failed to save address:', error);
      const message = error instanceof ApiError ? error.message : 'Failed to save address';
      toast({
        title: 'Error',
        description: message,
        variant: 'destructive',
      });
    } finally {
      setIsSaving(false);
    }
  };

  const handleDeleteAddress = async () => {
    if (!deleteAddressId) return;

    try {
      await api.deleteAddress(deleteAddressId);
      toast({
        title: 'Success',
        description: 'Address deleted successfully',
      });
      await loadAddresses();
    } catch (error) {
      console.error('[v0] Failed to delete address:', error);
      const message = error instanceof ApiError ? error.message : 'Failed to delete address';
      toast({
        title: 'Error',
        description: message,
        variant: 'destructive',
      });
    } finally {
      setDeleteAddressId(null);
    }
  };

  const openAddressDialog = (address?: Address) => {
    if (address) {
      setEditingAddress(address);
      setAddressData({
        street_line1: address.street_line1,
        street_line2: address.street_line2 || '',
        city: address.city,
        state_region: address.state_region,
        postal_code: address.postal_code,
        country: address.country,
        is_default_shipping: address.is_default_shipping,
      });
    } else {
      resetAddressForm();
    }
    setAddressDialogOpen(true);
  };

  const resetAddressForm = () => {
    setEditingAddress(null);
    setAddressData({
      street_line1: '',
      street_line2: '',
      city: '',
      state_region: '',
      postal_code: '',
      country: '',
      is_default_shipping: false,
    });
  };

  if (authLoading || !user) {
    return (
      <div className="container mx-auto px-4 py-8">
        <p className="text-center text-muted-foreground">Loading account...</p>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-8 max-w-4xl">
      <h1 className="text-3xl font-bold mb-8">Account Settings</h1>

      <Tabs defaultValue="profile" className="space-y-6">
        <TabsList>
          <TabsTrigger value="profile">Profile</TabsTrigger>
          <TabsTrigger value="addresses">Addresses</TabsTrigger>
        </TabsList>

        <TabsContent value="profile">
          <Card>
            <CardHeader>
              <CardTitle>Profile Information</CardTitle>
              <CardDescription>Update your personal details</CardDescription>
            </CardHeader>
            <CardContent>
              <form onSubmit={handleUpdateProfile} className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="first_name">First Name</Label>
                    <Input
                      id="first_name"
                      required
                      value={profileData.first_name}
                      onChange={(e) =>
                        setProfileData({ ...profileData, first_name: e.target.value })
                      }
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="last_name">Last Name</Label>
                    <Input
                      id="last_name"
                      required
                      value={profileData.last_name}
                      onChange={(e) =>
                        setProfileData({ ...profileData, last_name: e.target.value })
                      }
                    />
                  </div>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="email">Email</Label>
                  <Input
                    id="email"
                    type="email"
                    required
                    value={profileData.email}
                    onChange={(e) =>
                      setProfileData({ ...profileData, email: e.target.value })
                    }
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="phone">Phone</Label>
                  <Input
                    id="phone"
                    type="tel"
                    required
                    value={profileData.phone}
                    onChange={(e) =>
                      setProfileData({ ...profileData, phone: e.target.value })
                    }
                  />
                </div>

                <div className="pt-4">
                  <Button type="submit" disabled={isSaving}>
                    {isSaving ? 'Saving...' : 'Save Changes'}
                  </Button>
                </div>
              </form>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="addresses">
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle>Shipping Addresses</CardTitle>
                  <CardDescription>Manage your delivery addresses</CardDescription>
                </div>
                <Dialog open={addressDialogOpen} onOpenChange={setAddressDialogOpen}>
                  <DialogTrigger asChild>
                    <Button onClick={() => openAddressDialog()}>
                      <Plus className="h-4 w-4 mr-2" />
                      Add Address
                    </Button>
                  </DialogTrigger>
                  <DialogContent className="max-w-2xl">
                    <DialogHeader>
                      <DialogTitle>
                        {editingAddress ? 'Edit Address' : 'Add New Address'}
                      </DialogTitle>
                      <DialogDescription>
                        {editingAddress
                          ? 'Update your shipping address details'
                          : 'Add a new shipping address to your account'}
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
                        <Button type="submit" disabled={isSaving} className="flex-1">
                          {isSaving ? 'Saving...' : editingAddress ? 'Update' : 'Add Address'}
                        </Button>
                        <Button
                          type="button"
                          variant="outline"
                          onClick={() => {
                            setAddressDialogOpen(false);
                            resetAddressForm();
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
            </CardHeader>
            <CardContent>
              {isLoading ? (
                <p className="text-center text-muted-foreground py-4">Loading addresses...</p>
              ) : addresses.length === 0 ? (
                <div className="text-center py-8">
                  <MapPin className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
                  <h3 className="text-lg font-semibold mb-2">No addresses yet</h3>
                  <p className="text-muted-foreground">
                    Add a shipping address to complete your orders
                  </p>
                </div>
              ) : (
                <div className="space-y-4">
                  {Array.isArray(addresses) && addresses.length > 0 ? (
                    addresses.map((address) => (
                    <div
                      key={address.id}
                      className="p-4 rounded-lg border flex items-start justify-between"
                    >
                      <div className="space-y-1">
                        <div className="flex items-center gap-2">
                          <MapPin className="h-4 w-4 text-muted-foreground" />
                          <p className="font-medium">{address.street_line1}</p>
                          {address.is_default_shipping && (
                            <span className="text-xs bg-primary/10 text-primary px-2 py-0.5 rounded">
                              Default
                            </span>
                          )}
                        </div>
                        {address.street_line2 && (
                          <p className="text-sm text-muted-foreground pl-6">
                            {address.street_line2}
                          </p>
                        )}
                        <p className="text-sm text-muted-foreground pl-6">
                          {address.city}, {address.state_region} {address.postal_code}
                        </p>
                        <p className="text-sm text-muted-foreground pl-6">
                          {address.country}
                        </p>
                      </div>
                      <div className="flex gap-2">
                        <Button
                          variant="ghost"
                          size="icon"
                          onClick={() => openAddressDialog(address)}
                        >
                          <Edit2 className="h-4 w-4" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="icon"
                          onClick={() => setDeleteAddressId(address.id)}
                        >
                          <Trash2 className="h-4 w-4" />
                        </Button>
                      </div>
                    </div>
                  ))
                  ) : (
                    <p className="text-center text-muted-foreground py-4">No addresses found</p>
                  )}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      <AlertDialog open={deleteAddressId !== null} onOpenChange={() => setDeleteAddressId(null)}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Delete Address</AlertDialogTitle>
            <AlertDialogDescription>
              Are you sure you want to delete this address? This action cannot be undone.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction onClick={handleDeleteAddress}>Delete</AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}
