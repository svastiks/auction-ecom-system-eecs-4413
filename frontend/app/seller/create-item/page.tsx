'use client';

import { useState, useEffect } from 'react';
import { api, Category, ItemInput, ApiError } from '@/lib/api';
import { useAuth } from '@/lib/auth-context';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { useToast } from '@/hooks/use-toast';
import { useRouter } from 'next/navigation';
import { ArrowLeft, X, Plus } from 'lucide-react';
import Link from 'next/link';
import { Checkbox } from '@/components/ui/checkbox';

export default function CreateItemPage() {
  const { user, isLoading: authLoading } = useAuth();
  const router = useRouter();
  const { toast } = useToast();
  const [categories, setCategories] = useState<Category[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [imageUrls, setImageUrls] = useState<string[]>(['']);

  const [formData, setFormData] = useState({
    title: '',
    description: '',
    category_id: '',
    keywords: '',
    base_price: '',
    shipping_price_normal: '',
    shipping_price_expedited: '',
    shipping_time_days: '',
    is_active: true,
  });

  useEffect(() => {
    if (!authLoading && !user) {
      router.push('/auth');
    }
  }, [user, authLoading, router]);

  useEffect(() => {
    loadCategories();
  }, []);

  const loadCategories = async () => {
    try {
      const categoriesData = await api.getCategories();
      setCategories(categoriesData);
    } catch (error) {
      console.error('[v0] Failed to load categories:', error);
      toast({
        title: 'Error',
        description: 'Failed to load categories',
        variant: 'destructive',
      });
    }
  };

  const handleImageUrlChange = (index: number, value: string) => {
    const newUrls = [...imageUrls];
    newUrls[index] = value;
    setImageUrls(newUrls);
  };

  const addImageUrl = () => {
    setImageUrls([...imageUrls, '']);
  };

  const removeImageUrl = (index: number) => {
    if (imageUrls.length > 1) {
      setImageUrls(imageUrls.filter((_, i) => i !== index));
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    // Validation
    if (!formData.title || !formData.description || !formData.category_id) {
      toast({
        title: 'Validation Error',
        description: 'Title, description, and category are required',
        variant: 'destructive',
      });
      return;
    }

    const validImageUrls = imageUrls.filter(url => url.trim() !== '');
    if (validImageUrls.length === 0) {
      toast({
        title: 'Validation Error',
        description: 'At least one image URL is required',
        variant: 'destructive',
      });
      return;
    }

    const base_price = Math.round(parseFloat(formData.base_price) * 100);
    const shipping_price_normal = Math.round(parseFloat(formData.shipping_price_normal) * 100);
    const shipping_price_expedited = Math.round(parseFloat(formData.shipping_price_expedited) * 100);

    if (isNaN(base_price) || base_price <= 0) {
      toast({
        title: 'Validation Error',
        description: 'Base price must be a valid positive number',
        variant: 'destructive',
      });
      return;
    }

    setIsLoading(true);

    try {
      const itemInput: ItemInput = {
        title: formData.title,
        description: formData.description,
        category_id: Number(formData.category_id),
        keywords: formData.keywords || undefined,
        base_price,
        shipping_price_normal,
        shipping_price_expedited,
        shipping_time_days: Number(formData.shipping_time_days),
        is_active: formData.is_active,
        images: validImageUrls.map((url, index) => ({
          url,
          position: index,
        })),
      };

      const createdItem = await api.createItem(itemInput);
      
      toast({
        title: 'Success',
        description: 'Item created successfully',
      });
      
      router.push(`/item/${createdItem.id}`);
    } catch (error) {
      console.error('[v0] Failed to create item:', error);
      const message = error instanceof ApiError ? error.message : 'Failed to create item';
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
          <CardTitle>Create New Item</CardTitle>
          <CardDescription>
            Add a new item to the catalogue to create auctions later
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-6">
            <div className="space-y-2">
              <Label htmlFor="title">Title *</Label>
              <Input
                id="title"
                required
                value={formData.title}
                onChange={(e) => setFormData({ ...formData, title: e.target.value })}
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="description">Description *</Label>
              <Textarea
                id="description"
                required
                rows={4}
                value={formData.description}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="category">Category *</Label>
              <Select
                value={formData.category_id}
                onValueChange={(value) => setFormData({ ...formData, category_id: value })}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Select a category" />
                </SelectTrigger>
                <SelectContent>
                  {categories.map((category) => (
                    <SelectItem key={category.id} value={String(category.id)}>
                      {category.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              {categories.length === 0 && (
                <p className="text-sm text-muted-foreground">
                  No categories available. Contact an admin to create categories.
                </p>
              )}
            </div>

            <div className="space-y-2">
              <Label htmlFor="keywords">Keywords</Label>
              <Input
                id="keywords"
                placeholder="jacket, winter, clothing"
                value={formData.keywords}
                onChange={(e) => setFormData({ ...formData, keywords: e.target.value })}
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="base_price">Base Price ($) *</Label>
                <Input
                  id="base_price"
                  type="number"
                  step="0.01"
                  min="0"
                  required
                  value={formData.base_price}
                  onChange={(e) => setFormData({ ...formData, base_price: e.target.value })}
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="shipping_time_days">Shipping Days *</Label>
                <Input
                  id="shipping_time_days"
                  type="number"
                  min="1"
                  required
                  value={formData.shipping_time_days}
                  onChange={(e) => setFormData({ ...formData, shipping_time_days: e.target.value })}
                />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="shipping_normal">Normal Shipping ($) *</Label>
                <Input
                  id="shipping_normal"
                  type="number"
                  step="0.01"
                  min="0"
                  required
                  value={formData.shipping_price_normal}
                  onChange={(e) =>
                    setFormData({ ...formData, shipping_price_normal: e.target.value })
                  }
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="shipping_expedited">Expedited Shipping ($) *</Label>
                <Input
                  id="shipping_expedited"
                  type="number"
                  step="0.01"
                  min="0"
                  required
                  value={formData.shipping_price_expedited}
                  onChange={(e) =>
                    setFormData({ ...formData, shipping_price_expedited: e.target.value })
                  }
                />
              </div>
            </div>

            <div className="space-y-2">
              <Label>Image URLs *</Label>
              {imageUrls.map((url, index) => (
                <div key={index} className="flex gap-2">
                  <Input
                    placeholder="https://example.com/image.jpg"
                    value={url}
                    onChange={(e) => handleImageUrlChange(index, e.target.value)}
                  />
                  {imageUrls.length > 1 && (
                    <Button
                      type="button"
                      variant="outline"
                      size="icon"
                      onClick={() => removeImageUrl(index)}
                    >
                      <X className="h-4 w-4" />
                    </Button>
                  )}
                </div>
              ))}
              <Button type="button" variant="outline" size="sm" onClick={addImageUrl}>
                <Plus className="h-4 w-4 mr-2" />
                Add Another Image
              </Button>
            </div>

            <div className="flex items-center space-x-2">
              <Checkbox
                id="is_active"
                checked={formData.is_active}
                onCheckedChange={(checked) =>
                  setFormData({ ...formData, is_active: checked as boolean })
                }
              />
              <Label htmlFor="is_active" className="cursor-pointer">
                Item is active
              </Label>
            </div>

            <div className="flex gap-3">
              <Button type="submit" disabled={isLoading} className="flex-1">
                {isLoading ? 'Creating...' : 'Create Item'}
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
