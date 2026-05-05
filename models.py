from pydantic import BaseModel
from typing import List, Optional

class Product(BaseModel):
    name: str
    category: str

class Brand(BaseModel):
    displayName: str
    description: str

class ReelPayload(BaseModel):
    id: int
    title: str
    videoUrl: str
    brand: Brand
    productReels: List[dict] = []
    createdAt: str
    numOfLikes: int = 0
    numOfWatches: int = 0

class ReelUpdatePayload(BaseModel):
    reelId: int
    likes: int
    watches: int

class UserPayload(BaseModel):
    id: str
    userReelViews: List[dict] = []
    userReelLikes: List[dict] = []