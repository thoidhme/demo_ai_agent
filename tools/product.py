import json

from tools.utils import RoutineResponse


def search_product(name: str):
    products = [
        {
            "modelName": "iPhone 16",
            "baseStorage": "128GB",
            "displaySize": "6.1-inch Super Retina XDR",
            "cameraMain": "48MP Wide, 12MP Ultra Wide",
            "chip": "A18 Bionic",
            "startingPriceUSD": 18000000,
            "variants": [
                    {
                        "storage": "256GB",
                        "priceUSD": 18000000
                    },
                {
                        "storage": "512GB",
                        "priceUSD": 20000000
                }
            ],
            "colors": ["Midnight", "Starlight", "Red", "Pink", "Green"]
        },
        {
            "modelName": "iPhone 16 Plus",
            "baseStorage": "128GB",
            "displaySize": "6.7-inch Super Retina XDR",
            "cameraMain": "48MP Wide, 12MP Ultra Wide",
            "chip": "A18 Bionic",
            "startingPriceUSD": 21000000,
            "variants": [
                    {
                        "storage": "256GB",
                        "priceUSD": 21000000
                    },
                {
                        "storage": "512GB",
                        "priceUSD": 30000000
                }
            ],
            "colors": ["Midnight", "Starlight", "Blue", "Pink", "Green"]
        },
        {
            "modelName": "iPhone 16 Pro",
            "baseStorage": "128GB",
            "displaySize": "6.3-inch Super Retina XDR with ProMotion",
            "cameraMain": "48MP Main (Pro), 12MP Ultra Wide, 12MP Telephoto (3x Optical Zoom)",
            "chip": "A18 Pro Bionic",
            "startingPriceUSD": 30000000,
            "variants": [
                    {
                        "storage": "256GB",
                        "priceUSD": 30000000
                    },
                {
                        "storage": "512GB",
                        "priceUSD": 34000000
                },
                {
                        "storage": "1TB",
                        "priceUSD": 38000000
                }
            ],
            "colors": ["Natural Titanium", "Blue Titanium", "Black Titanium"]
        },
        {
            "modelName": "iPhone 16 Pro Max",
            "baseStorage": "256GB",
            "displaySize": "6.9-inch Super Retina XDR with ProMotion",
            "cameraMain": "48MP Main (Pro), 12MP Ultra Wide, 12MP Telephoto (5x Optical Zoom)",
            "chip": "A18 Pro Bionic",
            "startingPriceUSD": 34000000,
            "variants": [
                    {
                        "storage": "512GB",
                        "priceUSD": 38000000
                    },
                {
                        "storage": "1TB",
                        "priceUSD": 40000000
                }
            ],
            "colors": ["Natural Titanium", "Blue Titanium", "White Titanium", ]
        }
    ]

    return RoutineResponse(json.dumps(products))
