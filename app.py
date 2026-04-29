from flask import Flask, request, jsonify
from flask_restful import Api, Resource, reqparse
from flask_cors import CORS
import requests, os
from dotenv import load_dotenv
import uuid


load_dotenv()

app = Flask(__name__)
CORS(app)
api = Api(app)

API_KEY = os.getenv("GOOGLE_API_KEY")
BASE_URL = "https://places.googleapis.com/v1"


class Autocomplete(Resource):
    def get(self):
        user_input = request.args.get("input")
        lat = request.args.get("lat")
        lng = request.args.get("lng")

        if not user_input or user_input.strip() == "":
            return {"error": "input required"}, 400
        
        session_token = request.args.get("sessionToken")

        if not session_token:
            session_token = str(uuid.uuid4())
        
        url = f"{BASE_URL}/places:autocomplete"

        headers = {
            "Content-Type": "application/json",
            "X-Goog-Api-Key": API_KEY,
            "X-Goog-FieldMask": (
                "suggestions.placePrediction.placeId,"
                "suggestions.placePrediction.text,"
                "suggestions.placePrediction.structuredFormat"
            )
        }

        body = {
            "input": user_input,
            "sessionToken": session_token
        }

        if lat and lng:
            body["locationBias"] = {
                "circle": {
                    "center": {
                        "latitude": float(lat),
                        "longitude": float(lng)
                    },
                    "radius": 50000
                }
            }

        res = requests.post(url, json=body, headers=headers)
        data = res.json()

        if "error" in data:
            return {"error": data["error"]}, 500

        suggestions = data.get("suggestions", [])

        results = [
            {
                "place_id": s["placePrediction"]["placeId"],
                "description": s["placePrediction"]["text"]["text"],
            }
            for s in suggestions
        ]

        return {"results": results}, 200

api.add_resource(Autocomplete, "/autocomplete")


class PlaceDetails(Resource):
    def get(self, place_id):
        url = f"{BASE_URL}/places/{place_id}"

        headers = {
            "Content-Type": "application/json",
            "X-Goog-Api-Key": API_KEY,
            "X-Goog-FieldMask": (
                "id,"
                "displayName,"
                "formattedAddress,"
                "rating,"
                "priceLevel,"
                "types,"
                "location"
            )
        }

        res = requests.get(url, headers=headers)
        data = res.json()

        return data, 200

api.add_resource(PlaceDetails, "/place/<string:place_id>")

class Places(Resource):
    def get(self):
        location = request.args.get("location")
        keyword = request.args.get("keyword", "")

        if not location or location.strip() == "":
            return {"error": "location is required (lat,lng)"}, 400
        
        try:
            lat, lng = map(float, location.split(","))
        except ValueError:
            return {"error": "location must be in format lat,lng"}, 400
        
        url = f"{BASE_URL}/places:searchNearby"

        headers = {
            "Content-Type": "application/json",
            "X-Goog-Api-Key": API_KEY,
            "X-Goog-FieldMask": "places.name,places.displayName,places.rating,places.formattedAddress"
        }

        body = {
            "maxResultCount": 10,
            "includedTypes": ["restaurant"],
            "locationRestriction": {
                "circle": {
                    "center": {
                        "latitude": lat,
                        "longitude": lng
                    },
                    "radius": 1500
                }
            }
        }

        response = requests.post(url, json=body, headers=headers)
        data = response.json()
        
        if "error" in data:
            print("GOOGLE ERROR:", data["error"])
            return {"error": data["error"]}, 500
        
        print("NEARBY RESPONSE:", data)

        places = data.get("places", [])

        results = [
            {
                "place_id": p["name"],
                "name": p["displayName"]["text"],
                "rating": p.get("rating"),
                "address": p.get("formattedAddress")
            }
            for p in places
        ]

        return {"results": results}, 200
    

api.add_resource(Places, "/places")