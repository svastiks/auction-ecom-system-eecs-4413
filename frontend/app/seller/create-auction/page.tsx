"use client"

import type React from "react"

import { useState, useEffect } from "react"
import { api, type Category, type ItemInput, type AuctionInput, ApiError } from "@/lib/api"
import { useAuth } from "@/lib/auth-context"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { useToast } from "@/hooks/use-toast"
import { useRouter } from "next/navigation"
import { ArrowLeft, X, Plus } from "lucide-react"
import Link from "next/link"
import { Checkbox } from "@/components/ui/checkbox"

export default function CreateAuctionPage() {
  const { user, isLoading: authLoading } = useAuth()
  const router = useRouter()
  const { toast } = useToast()
  const [categories, setCategories] = useState<Category[]>([])
  console.log(categories)
  const [isLoading, setIsLoading] = useState(false)
  const [imageUrls, setImageUrls] = useState<string[]>([""])

  const [itemData, setItemData] = useState({
    title: "",
    description: "",
    category_id: "",
    keywords: "",
    shipping_price_normal: "",
    shipping_price_expedited: "",
    shipping_time_days: "",
    is_active: true,
  })

  const [auctionData, setAuctionData] = useState({
    starting_price: "",
    min_increment: "1",
    start_time: "",
    end_time: "",
  })

  useEffect(() => {
    if (!authLoading && !user) {
      router.push("/auth")
    }
  }, [user, authLoading, router])

  useEffect(() => {
    loadCategories()
    // Set default times
    const now = new Date()
    const start = new Date(now.getTime() + 5 * 60000) // 5 minutes from now
    const end = new Date(now.getTime() + 7 * 24 * 60 * 60000) // 7 days from now

    setAuctionData((prev) => ({
      ...prev,
      start_time: start.toISOString().slice(0, 16),
      end_time: end.toISOString().slice(0, 16),
    }))
  }, [])

  const loadCategories = async () => {
    try {
      const categoriesData = await api.getCategories()
      setCategories(categoriesData)
    } catch (error) {
      console.error("Failed to load categories:", error)
      toast({
        title: "Error",
        description: "Failed to load categories",
        variant: "destructive",
      })
    }
  }

  const handleImageUrlChange = (index: number, value: string) => {
    const newUrls = [...imageUrls]
    newUrls[index] = value
    setImageUrls(newUrls)
  }

  const addImageUrl = () => {
    setImageUrls([...imageUrls, ""])
  }

  const removeImageUrl = (index: number) => {
    if (imageUrls.length > 1) {
      setImageUrls(imageUrls.filter((_, i) => i !== index))
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
  
    // Validation - Item fields
    if (!itemData.title || !itemData.description || !itemData.category_id) {
      toast({
        title: "Validation Error",
        description: "Title, description, and category are required",
        variant: "destructive",
      });
      return;
    }
  
    const validImageUrls = imageUrls.filter((url) => url.trim() !== "");
    if (validImageUrls.length === 0) {
      toast({
        title: "Validation Error",
        description: "At least one image URL is required",
        variant: "destructive",
      });
      return;
    }
  
    const shipping_price_normal = Math.round(Number.parseFloat(itemData.shipping_price_normal) * 100);
    const shipping_price_expedited = Math.round(Number.parseFloat(itemData.shipping_price_expedited) * 100);
  
    // Validation - Auction fields
    const starting_price = Math.round(Number.parseFloat(auctionData.starting_price) * 100);
    const min_increment = Math.round(Number.parseFloat(auctionData.min_increment) * 100);
  
    if (isNaN(starting_price) || starting_price <= 0) {
      toast({
        title: "Validation Error",
        description: "Starting price must be a valid positive number",
        variant: "destructive",
      });
      return;
    }
  
    if (min_increment < 100) {
      toast({
        title: "Validation Error",
        description: "Minimum increment must be at least $1",
        variant: "destructive",
      });
      return;
    }
  
    // datetime-local returns local time without timezone, so we need to treat it as local and convert to UTC
    // The input format is "YYYY-MM-DDTHH:mm" (local time)
    const startTimeLocal = new Date(auctionData.start_time);
    const endTimeLocal = new Date(auctionData.end_time);
    
    // Validate times are in the future (using local time comparison)
    const nowLocal = new Date();
    if (startTimeLocal <= nowLocal) {
      toast({
        title: "Validation Error",
        description: "Start time must be in the future",
        variant: "destructive",
      });
      return;
    }
  
    if (startTimeLocal >= endTimeLocal) {
      toast({
        title: "Validation Error",
        description: "End time must be after start time",
        variant: "destructive",
      });
      return;
    }
  
    if (endTimeLocal <= nowLocal) {
      toast({
        title: "Validation Error",
        description: "End time must be in the future",
        variant: "destructive",
      });
      return;
    }
  
    setIsLoading(true);
  
    try {
      // Validate category_id is not empty
      if (!itemData.category_id || itemData.category_id === '') {
        toast({
          title: "Validation Error",
          description: "Please select a category",
          variant: "destructive",
        });
        setIsLoading(false);
        return;
      }

      // Create Item - category_id is UUID string, not number
      const itemInput: ItemInput = {
        title: itemData.title,
        description: itemData.description,
        category_id: itemData.category_id, // Keep as UUID string, don't convert to number
        keywords: itemData.keywords || undefined,
        shipping_price_normal,
        shipping_price_expedited,
        shipping_time_days: Number(itemData.shipping_time_days),
        is_active: itemData.is_active,
        images: validImageUrls.map((url, index) => ({
          url,
          position: index,
        })),
        base_price: starting_price, // Include base_price using starting_price
      };
  
      const createdItem = await api.createItem(itemInput);
      console.log("Created Item Response:", createdItem);

      // Extract item_id - backend returns UUID as item_id or id
      const itemId = createdItem.id || (createdItem as any).item_id;
      
      if (!itemId) {
        console.error("Item response:", createdItem);
        throw new Error(`Failed to get item ID from API response. Response: ${JSON.stringify(createdItem)}`);
      }

      console.log("Creating auction with item_id:", itemId);
      console.log("Start time (local):", startTimeLocal);
      console.log("Start time (ISO):", startTimeLocal.toISOString());
      console.log("End time (local):", endTimeLocal);
      console.log("End time (ISO):", endTimeLocal.toISOString());

      // Create Auction - item_id must be UUID string
      // Convert local times to ISO strings (which will be in UTC)
      const auctionInput: AuctionInput = {
        auction_type: "FORWARD",
        starting_price,
        min_increment,
        start_time: startTimeLocal.toISOString(),
        end_time: endTimeLocal.toISOString(),
        status: "ACTIVE",
        item_id: String(itemId), // Ensure it's a string (UUID)
      };
  
      console.log("Auction input:", JSON.stringify(auctionInput, null, 2));
      const createdAuction = await api.createAuction(auctionInput);
      console.log("Created Auction Response:", createdAuction);
  
      const auctionId = createdAuction.id || (createdAuction as any).auction_id;
  
      toast({
        title: "Success",
        description: "Item and auction created successfully",
      });
  
      router.push(`/auction/${auctionId}`);
    } catch (error) {
      console.error("Failed to create item/auction:", error);
      let errorMessage = "Failed to create item and auction";
      if (error instanceof ApiError) {
        errorMessage = error.message || error.data?.detail || error.data?.message || `Error: ${error.status}`;
      } else if (error instanceof Error) {
        errorMessage = error.message;
      }
      toast({
        title: "Error",
        description: errorMessage,
        variant: "destructive",
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
          <CardTitle>Create Item and Auction</CardTitle>
          <CardDescription>Create a new item and start an auction for it</CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-8">
            <div className="space-y-4">
              <h3 className="text-lg font-semibold">Item Details</h3>

              <div className="space-y-2">
                <Label htmlFor="title">Title *</Label>
                <Input
                  id="title"
                  required
                  value={itemData.title}
                  onChange={(e) => setItemData({ ...itemData, title: e.target.value })}
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="description">Description *</Label>
                <Textarea
                  id="description"
                  required
                  rows={4}
                  value={itemData.description}
                  onChange={(e) => setItemData({ ...itemData, description: e.target.value })}
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="category">Category *</Label>
                <Select
                  value={itemData.category_id || undefined}
                  onValueChange={(value) => setItemData({ ...itemData, category_id: value })}
                >
                  <SelectTrigger id="category">
                    <SelectValue placeholder="Select a category" />
                  </SelectTrigger>
                  <SelectContent>
                    {categories.map((category) => {
                      const categoryId = String(category.id || category.category_id || '');
                      return (
                        <SelectItem key={categoryId} value={categoryId}>
                          {category.name}
                        </SelectItem>
                      );
                    })}
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                <Label htmlFor="keywords">Keywords</Label>
                <Input
                  id="keywords"
                  placeholder="jacket, winter, clothing"
                  value={itemData.keywords}
                  onChange={(e) => setItemData({ ...itemData, keywords: e.target.value })}
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="shipping_time_days">Shipping Days *</Label>
                  <Input
                    id="shipping_time_days"
                    type="number"
                    min="1"
                    required
                    value={itemData.shipping_time_days}
                    onChange={(e) => setItemData({ ...itemData, shipping_time_days: e.target.value })}
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="shipping_normal">Normal Shipping ($) *</Label>
                  <Input
                    id="shipping_normal"
                    type="number"
                    step="0.01"
                    min="0"
                    required
                    value={itemData.shipping_price_normal}
                    onChange={(e) => setItemData({ ...itemData, shipping_price_normal: e.target.value })}
                  />
                </div>
              </div>

              <div className="space-y-2">
                <Label htmlFor="shipping_expedited">Expedited Shipping ($) *</Label>
                <Input
                  id="shipping_expedited"
                  type="number"
                  step="0.01"
                  min="0"
                  required
                  value={itemData.shipping_price_expedited}
                  onChange={(e) => setItemData({ ...itemData, shipping_price_expedited: e.target.value })}
                />
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
                      <Button type="button" variant="outline" size="icon" onClick={() => removeImageUrl(index)}>
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
                  checked={itemData.is_active}
                  onCheckedChange={(checked) => setItemData({ ...itemData, is_active: checked as boolean })}
                />
                <Label htmlFor="is_active" className="cursor-pointer">
                  Item is active
                </Label>
              </div>
            </div>

            <div className="space-y-4 border-t pt-6">
              <h3 className="text-lg font-semibold">Auction Details</h3>

              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="starting_price">Starting Price ($) *</Label>
                  <Input
                    id="starting_price"
                    type="number"
                    step="0.01"
                    min="0"
                    required
                    value={auctionData.starting_price}
                    onChange={(e) => setAuctionData({ ...auctionData, starting_price: e.target.value })}
                  />
                  <p className="text-xs text-muted-foreground">This will be the item's base price</p>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="min_increment">Min Increment ($) *</Label>
                  <Input
                    id="min_increment"
                    type="number"
                    step="0.01"
                    min="1"
                    required
                    value={auctionData.min_increment}
                    onChange={(e) => setAuctionData({ ...auctionData, min_increment: e.target.value })}
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="start_time">Start Time *</Label>
                  <Input
                    id="start_time"
                    type="datetime-local"
                    required
                    value={auctionData.start_time}
                    onChange={(e) => setAuctionData({ ...auctionData, start_time: e.target.value })}
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="end_time">End Time *</Label>
                  <Input
                    id="end_time"
                    type="datetime-local"
                    required
                    value={auctionData.end_time}
                    onChange={(e) => setAuctionData({ ...auctionData, end_time: e.target.value })}
                  />
                </div>
              </div>
            </div>

            <div className="flex gap-3">
              <Button type="submit" disabled={isLoading} className="flex-1">
                {isLoading ? "Creating..." : "Create Item & Auction"}
              </Button>
              <Link href="/catalogue" className="flex-1">
                <Button type="button" variant="outline" className="w-full bg-transparent">
                  Cancel
                </Button>
              </Link>
            </div>
          </form>
        </CardContent>
      </Card>
    </div>
  )
}
