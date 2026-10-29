#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import torch
import torch.nn as nn
from torchvision import models
from torchvision.transforms.v2 import Compose, ToImage, ToDtype, Resize, Normalize

gpu_id = 0 # Change to your desired GPU index (e.g., 0, 1, 2)
device = torch.device(f"cuda:{gpu_id}" if torch.cuda.is_available() else "cpu")

model_path = f'{os.getenv("HOME")}/Data/models/dogcat_vgg16_finetuned.pt'

#%%

IMG_H, IMG_W = 180, 180

imagenet_mean = [0.485, 0.456, 0.406]
imagenet_std = [0.229, 0.224, 0.225]
normalizer_imagenet = Normalize(mean=imagenet_mean, std=imagenet_std)

conv_base = models.vgg16(weights=models.VGG16_Weights.IMAGENET1K_V1).features
conv_base.to(device)
conv_base.eval() # since conv_base won't be trained, set it to evaluation (inference) mode to ensure layers like Dropout behave correctly
for p in conv_base.parameters():
    p.requires_grad = False
   
class VGG16Frozen(nn.Module):
    def __init__(self, conv_base):
        super().__init__()
        self.conv_base = conv_base        
        with torch.no_grad():
            dummy = torch.zeros(1, 3, IMG_H, IMG_W).to(next(conv_base.parameters()).device)
            flat_dim = self.conv_base(dummy).numel()
        self.fc1 = nn.Linear(flat_dim, 256)
        self.dropout = nn.Dropout(p=0.5)
        self.fc2 = nn.Linear(256, 2)

    def forward(self, x):
        x = self.conv_base(x)
        x = torch.flatten(x, 1)
        x = self.fc1(x)
        x = self.dropout(x)
        x = self.fc2(x)
        return x

model = VGG16Frozen(conv_base).to(device)
model.load_state_dict(torch.load(model_path, map_location=device))

def predict( img ):
    img_tensor = Compose( [ Resize( (IMG_H, IMG_W) ), ToImage(), ToDtype(torch.float32, scale=True)] )(img).unsqueeze(0) # unsqueeze to form a single-instance batch
    with torch.no_grad():
        p =torch.sigmoid( model(img_tensor.to(device) ).squeeze() ) # squeeze to remove batch dimension
    return p[1].item()    