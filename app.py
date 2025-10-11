from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import json
import os
import random
import math
from difflib import get_close_matches

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes
with open("india_tourism_full_dataset.json", "r", encoding="utf-8") as f:
    tourism_data = json.load(f)

# Add region information to the dataset if not present
region_mapping = {
    "North": ["Jammu and Kashmir", "Ladakh", "Himachal Pradesh", "Uttarakhand", "Punjab", "Haryana", "Delhi", "Uttar Pradesh"],
    "South": ["Karnataka", "Tamil Nadu", "Kerala", "Andhra Pradesh", "Telangana", "Puducherry"],
    "East": ["Bihar", "Jharkhand", "West Bengal", "Odisha"],
    "West": ["Rajasthan", "Gujarat", "Maharashtra", "Goa", "Dadra and Nagar Haveli and Daman and Diu"],
    "Central": ["Madhya Pradesh", "Chhattisgarh"],
    "North East": ["Sikkim", "Assam", "Meghalaya", "Arunachal Pradesh", "Nagaland", "Manipur", "Mizoram", "Tripura"]
}

# Add region to each state in the dataset
for entry in tourism_data:
    for region, states in region_mapping.items():
        if entry["state"] in states:
            entry["region"] = region
            break
    if "region" not in entry:
        entry["region"] = "Other"  # For union territories or other areas

STATES_AND_UTS = [
    # States
    "Andhra Pradesh", "Arunachal Pradesh", "Assam", "Bihar", 
    "Chhattisgarh", "Goa", "Gujarat", "Haryana", "Himachal Pradesh", 
    "Jharkhand", "Karnataka", "Kerala", "Madhya Pradesh", "Maharashtra", 
    "Manipur", "Meghalaya", "Mizoram", "Nagaland", "Odisha", "Punjab", 
    "Rajasthan", "Sikkim", "Tamil Nadu", "Telangana", "Tripura", 
    "Uttar Pradesh", "Uttarakhand", "West Bengal",
    # Union Territories
    "Andaman and Nicobar Islands", "Chandigarh", "Dadra and Nagar Haveli and Daman and Diu", 
    "Delhi", "Jammu and Kashmir", "Ladakh", "Lakshadweep", "Puducherry"
]

# Geographical coordinates (latitude, longitude) of state/UT capitals
COORDINATES = {
    "Andhra Pradesh": (16.5062, 80.6480),  # Amaravati
    "Arunachal Pradesh": (27.0844, 93.6053),  # Itanagar
    "Assam": (26.1433, 91.7898),  # Dispur
    "Bihar": (25.5941, 85.1376),  # Patna
    "Chhattisgarh": (21.2514, 81.6296),  # Raipur
    "Goa": (15.4909, 73.8278),  # Panaji
    "Gujarat": (23.2156, 72.6369),  # Gandhinagar
    "Haryana": (30.7333, 76.7794),  # Chandigarh
    "Himachal Pradesh": (31.1048, 77.1734),  # Shimla
    "Jharkhand": (23.3441, 85.3096),  # Ranchi
    "Karnataka": (12.9716, 77.5946),  # Bengaluru
    "Kerala": (8.5241, 76.9366),  # Thiruvananthapuram
    "Madhya Pradesh": (23.2599, 77.4126),  # Bhopal
    "Maharashtra": (19.0760, 72.8777),  # Mumbai
    "Manipur": (24.8170, 93.9368),  # Imphal
    "Meghalaya": (25.5788, 91.8933),  # Shillong
    "Mizoram": (23.7307, 92.7173),  # Aizawl
    "Nagaland": (25.6751, 94.1086),  # Kohima
    "Odisha": (20.2961, 85.8245),  # Bhubaneswar
    "Punjab": (30.7333, 76.7794),  # Chandigarh
    "Rajasthan": (26.9124, 75.7873),  # Jaipur
    "Sikkim": (27.3389, 88.6065),  # Gangtok
    "Tamil Nadu": (13.0827, 80.2707),  # Chennai
    "Telangana": (17.3850, 78.4867),  # Hyderabad
    "Tripura": (23.8315, 91.2868),  # Agartala
    "Uttar Pradesh": (26.8467, 80.9462),  # Lucknow
    "Uttarakhand": (30.3165, 78.0322),  # Dehradun
    "West Bengal": (22.5726, 88.3639),  # Kolkata
    "Andaman and Nicobar Islands": (11.6234, 92.7265),  # Port Blair
    "Chandigarh": (30.7333, 76.7794),  # Chandigarh
    "Dadra and Nagar Haveli and Daman and Diu": (20.1809, 73.0169),  # Daman
    "Delhi": (28.6139, 77.2090),  # New Delhi
    "Jammu and Kashmir": (34.0837, 74.7973),  # Srinagar
    "Ladakh": (34.1526, 77.5770),  # Leh
    "Lakshadweep": (10.5667, 72.6417),  # Kavaratti
    "Puducherry": (11.9416, 79.8083)  # Puducherry
}

# State-specific cost modifiers (1 is average, <1 is cheaper, >1 is more expensive)
STATE_COST_MODIFIERS = {
    "Andhra Pradesh": 0.9,
    "Arunachal Pradesh": 1.2,
    "Assam": 0.85,
    "Bihar": 0.75,
    "Chhattisgarh": 0.8,
    "Goa": 1.3,
    "Gujarat": 0.95,
    "Haryana": 1.0,
    "Himachal Pradesh": 1.05,
    "Jharkhand": 0.8,
    "Karnataka": 1.1,
    "Kerala": 1.05,
    "Madhya Pradesh": 0.85,
    "Maharashtra": 1.15,
    "Manipur": 0.9,
    "Meghalaya": 0.95,
    "Mizoram": 0.95,
    "Nagaland": 0.9,
    "Odisha": 0.8,
    "Punjab": 0.9,
    "Rajasthan": 0.85,
    "Sikkim": 1.1,
    "Tamil Nadu": 0.95,
    "Telangana": 1.0,
    "Tripura": 0.85,
    "Uttar Pradesh": 0.8,
    "Uttarakhand": 1.0,
    "West Bengal": 0.9,
    "Andaman and Nicobar Islands": 1.4,
    "Chandigarh": 1.1,
    "Dadra and Nagar Haveli and Daman and Diu": 1.05,
    "Delhi": 1.2,
    "Jammu and Kashmir": 1.1,
    "Ladakh": 1.25,
    "Lakshadweep": 1.5,
    "Puducherry": 1.0
}

# Tourism places by state/UT
TOURISM_PLACES = {
    "Andhra Pradesh": ["Tirupati", "Visakhapatnam", "Araku Valley", "Gandikota", "Borra Caves", "Horsley Hills"],
    "Arunachal Pradesh": ["Tawang", "Ziro Valley", "Sela Pass", "Namdapha National Park", "Bumla Pass"],
    "Assam": ["Kaziranga National Park", "Majuli Island", "Kamakhya Temple", "Manas Wildlife Sanctuary", "Hajo"],
    "Bihar": ["Bodh Gaya", "Nalanda", "Rajgir", "Vaishali", "Pawapuri", "Patna Sahib"],
    "Chhattisgarh": ["Chitrakote Falls", "Tirathgarh Falls", "Barnawapara Wildlife Sanctuary", "Bastar", "Sirpur"],
    "Goa": ["Calangute Beach", "Baga Beach", "Dudhsagar Falls", "Fort Aguada", "Basilica of Bom Jesus", "Anjuna Beach"],
    "Gujarat": ["Rann of Kutch", "Somnath Temple", "Gir National Park", "Dwarka", "Statue of Unity", "Sabarmati Ashram"],
    "Haryana": ["Sultanpur Bird Sanctuary", "Kurukshetra", "Pinjore Gardens", "Tilyar Lake", "Badkhal Lake"],
    "Himachal Pradesh": ["Shimla", "Manali", "Dharamshala", "Dalhousie", "Kasol", "Spiti Valley", "Khajjiar"],
    "Jharkhand": ["Patratu Valley", "Netarhat", "Baidyanath Jyotirlinga Temple", "Hundru Falls", "Dalma Wildlife Sanctuary"],
    "Karnataka": ["Bangalore", "Mysore Palace", "Hampi", "Coorg", "Gokarna", "Jog Falls", "Bandipur National Park"],
    "Kerala": ["Alleppey", "Munnar", "Kumarakom", "Wayanad", "Kovalam Beach", "Thekkady", "Fort Kochi"],
    "Madhya Pradesh": ["Khajuraho", "Bandhavgarh National Park", "Sanchi Stupa", "Orchha", "Ujjain", "Kanha National Park"],
    "Maharashtra": ["Mumbai", "Ajanta & Ellora Caves", "Mahabaleshwar", "Lonavala", "Shirdi", "Elephanta Caves"],
    "Manipur": ["Loktak Lake", "Keibul Lamjao National Park", "Ima Keithel", "Kangla Fort", "Shirui Hills"],
    "Meghalaya": ["Cherrapunji", "Shillong", "Dawki", "Mawlynnong", "Double Decker Living Root Bridge", "Mawsynram"],
    "Mizoram": ["Aizawl", "Phawngpui Blue Mountain", "Dampa Tiger Reserve", "Reiek", "Vantawng Falls"],
    "Nagaland": ["Kohima", "Dzukou Valley", "Khonoma Village", "Mon", "Naga Heritage Village", "Intangki National Park"],
    "Odisha": ["Konark Sun Temple", "Puri Jagannath Temple", "Chilika Lake", "Lingaraja Temple", "Udayagiri and Khandagiri Caves"],
    "Punjab": ["Golden Temple", "Jallianwala Bagh", "Wagah Border", "Harike Wetland", "Anandpur Sahib"],
    "Rajasthan": ["Jaipur", "Udaipur", "Jaisalmer", "Jodhpur", "Pushkar", "Ranthambore National Park", "Mount Abu"],
    "Sikkim": ["Gangtok", "Nathula Pass", "Yumthang Valley", "Tsomgo Lake", "Pelling", "Kanchenjunga Base Camp"],
    "Tamil Nadu": ["Chennai", "Ooty", "Kodaikanal", "Madurai Meenakshi Temple", "Rameshwaram", "Mahabalipuram"],
    "Telangana": ["Hyderabad", "Ramoji Film City", "Warangal Fort", "Nagarjuna Sagar", "Golconda Fort", "Charminar"],
    "Tripura": ["Ujjayanta Palace", "Neermahal", "Unakoti", "Tripura Sundari Temple", "Sepahijala Wildlife Sanctuary"],
    "Uttar Pradesh": ["Taj Mahal", "Varanasi", "Prayagraj", "Mathura", "Ayodhya", "Sarnath", "Lucknow"],
    "Uttarakhand": ["Rishikesh", "Haridwar", "Nainital", "Mussoorie", "Auli", "Valley of Flowers", "Kedarnath"],
    "West Bengal": ["Kolkata", "Darjeeling", "Sundarbans", "Digha", "Kalimpong", "Siliguri", "Dooars"],
    "Andaman and Nicobar Islands": ["Radhanagar Beach", "Cellular Jail", "Ross Island", "Havelock Island", "Neil Island", "Barren Island"],
    "Chandigarh": ["Rock Garden", "Sukhna Lake", "Rose Garden", "Capitol Complex", "Leisure Valley"],
    "Dadra and Nagar Haveli and Daman and Diu": ["Devka Beach", "Fort of Diu", "Nagoa Beach", "St. Paul's Church", "Daman Ganga Tourist Complex"],
    "Delhi": ["Red Fort", "Qutub Minar", "India Gate", "Humayun's Tomb", "Lotus Temple", "Akshardham Temple"],
    "Jammu and Kashmir": ["Dal Lake", "Gulmarg", "Pahalgam", "Sonamarg", "Vaishno Devi", "Mughal Gardens"],
    "Ladakh": ["Pangong Lake", "Nubra Valley", "Magnetic Hill", "Leh Palace", "Hemis Monastery", "Zanskar Valley"],
    "Lakshadweep": ["Agatti Island", "Bangaram Island", "Kavaratti Island", "Kalpeni Island", "Minicoy Island"],
    "Puducherry": ["Auroville", "Paradise Beach", "French Quarter", "Chunnambar Boat House", "Serenity Beach"]
}
def month_to_number(month):
    if not month:
        return None
    months = ["January", "February", "March", "April", "May", "June",
              "July", "August", "September", "October", "November", "December"]
    month_str = month.capitalize()
    return months.index(month_str) + 1 if month_str in months else None

# Month number to name (for output formatting)
def month_number_to_name(month_num):
    if not month_num or month_num < 1 or month_num > 12:
        return None
    return ["January", "February", "March", "April", "May", "June",
            "July", "August", "September", "October", "November", "December"][month_num - 1]

# Function to determine if a destination is suitable for a given month
def is_suitable_for_month(best_time_str, month_num):
    if not month_num or not best_time_str:
        return True  # If no month specified, all destinations are suitable
    
    month_names = {
        1: "january", 2: "february", 3: "march", 4: "april",
        5: "may", 6: "june", 7: "july", 8: "august",
        9: "september", 10: "october", 11: "november", 12: "december"
    }
    
    selected_month = month_names.get(month_num, "").lower()
    best_time = best_time_str.lower()
    
    # Direct month mention
    if selected_month in best_time:
        return True
    
    # Debug
    print(f"Checking month {selected_month} against best time: {best_time}")
        
    # Handle ranges like "October to March"
    if "to" in best_time:
        parts = best_time.split("to")
        start_month = parts[0].strip()
        end_month = parts[1].strip()
        
        # Find closest matching months
        all_months = list(month_names.values())
        start = get_close_matches(start_month, all_months, n=1)
        end = get_close_matches(end_month, all_months, n=1)
        
        # Function to determine if a destination is suitable for a given month
def is_suitable_for_month(best_time_str, month_num):
    if not month_num or not best_time_str:
        return True  # If no month specified, all destinations are suitable
    
    month_names = {
        1: "january", 2: "february", 3: "march", 4: "april",
        5: "may", 6: "june", 7: "july", 8: "august",
        9: "september", 10: "october", 11: "november", 12: "december"
    }
    
    selected_month = month_names.get(month_num, "").lower()
    best_time = best_time_str.lower()
    
    # Direct month mention
    if selected_month in best_time:
        return True
    
    # Debug
    print(f"Checking month {selected_month} against best time: {best_time}")
        
    # Handle ranges like "October to March"
    if "to" in best_time:
        parts = best_time.split("to")
        start_month = parts[0].strip()
        end_month = parts[1].strip()
        
        # Find closest matching months
        all_months = list(month_names.values())
        start = get_close_matches(start_month, all_months, n=1)
        end = get_close_matches(end_month, all_months, n=1)
        
        if start and end:
            start_idx = list(month_names.values()).index(start[0]) + 1
            end_idx = list(month_names.values()).index(end[0]) + 1
            
            # Debug
            print(f"Start month: {start[0]} (index {start_idx}), End month: {end[0]} (index {end_idx}), Selected month: {month_num}")
            
            # Handle wrapping around the year (e.g., "October to March")
            if start_idx > end_idx:  # Wraps around year end
                is_suitable = month_num >= start_idx or month_num <= end_idx
                print(f"Wrapping case: {is_suitable}")
                return is_suitable
            else:
                is_suitable = start_idx <= month_num <= end_idx
                print(f"Non-wrapping case: {is_suitable}")
                return is_suitable
    
    # Handle comma separated ranges like "March to June, September to December"
    if "," in best_time:
        for period in best_time.split(","):
            if is_suitable_for_month(period.strip(), month_num):
                return True
                
    return False

# Add this function near the other helper functions
def generate_targeted_feedback(user_input, constraints, region_filtered):
    """Generate targeted feedback based on constraints"""
    feedback = {}
    region = user_input.get("region")
    preferred_month = user_input.get("preferred_month")
    interests = user_input.get("interests", [])
    
    # Count constraint types
    constraint_counts = {}
    constraint_messages = {
        "region": [],
        "month": [],
        "interests": []
    }
    
    for constraint in constraints:
        constraint_type = constraint["type"]
        if constraint_type in constraint_counts:
            constraint_counts[constraint_type] += 1
            constraint_messages[constraint_type].append(constraint["message"])
        else:
            constraint_counts[constraint_type] = 1
            constraint_messages[constraint_type] = [constraint["message"]]
    
    # Generate specific feedback based on constraint types
    suggestions = []
    
    # Month-specific feedback
    if "month" in constraint_counts and preferred_month:
        # Extract best time recommendations from top destinations
        best_times = []
        for dest in region_filtered[:3]:
            if dest.get("best_time") and dest.get("best_time") not in best_times:
                best_times.append(dest.get("best_time"))
        
        if best_times:
            feedback["month_issue"] = True
            feedback["message"] = f"{preferred_month} may not be ideal for your selected destinations."
            suggestions.append(f"Consider visiting during {', '.join(best_times)}")
    
    # Region-specific feedback
    if "region" in constraint_counts and region and region != "Any":
        # Find regions that better match their interests
        interest_regions = {}
        for dest in region_filtered:
            r = dest.get("region")
            if r != region and "score_breakdown" in dest:
                interest_score = dest.get("score_breakdown", {}).get("interest_match", 0)
                if r not in interest_regions:
                    interest_regions[r] = interest_score
                else:
                    interest_regions[r] = max(interest_regions[r], interest_score)
        
        # Recommend regions with better interest matches
        if interest_regions:
            best_regions = sorted(interest_regions.items(), key=lambda x: x[1], reverse=True)[:2]
            if best_regions[0][1] > 0:
                better_regions = [r[0] for r in best_regions if r[1] > 0]
                if better_regions:
                    suggestions.append(f"Consider {', '.join(better_regions)} which better match your interests")
    
    # Interest-specific feedback
    if "interests" in constraint_counts and interests:
        # Analyze which interests are problematic
        unmatched_interests = []
        matched_interests = []
        
        for dest in region_filtered[:3]:
            if "score_breakdown" in dest:
                unmatched = dest.get("score_breakdown", {}).get("unmatched_interests", [])
                matched = dest.get("score_breakdown", {}).get("matched_interests", [])
                
                for interest in unmatched:
                    if interest not in unmatched_interests:
                        unmatched_interests.append(interest)
                
                for interest in matched:
                    if interest not in matched_interests:
                        matched_interests.append(interest)
        
        # Suggest removing problematic interests
        if unmatched_interests and region != "Any":
            feedback["interest_issue"] = True
            feedback["problematic_interests"] = unmatched_interests
            feedback["message"] = f"{region} region may not be ideal for: {', '.join(unmatched_interests)}"
            
            if matched_interests:
                suggestions.append(f"Focus on these interests instead: {', '.join(matched_interests)}")
            if len(unmatched_interests) > 1:
                suggestions.append(f"Remove some interests like {', '.join(unmatched_interests[:2])}")
            suggestions.append("Or select 'Any' for region to find better matches")
    
    # Add suggestions to feedback
    if suggestions:
        feedback["suggestions"] = suggestions
    
    return feedback

# Calculate relevance score for destination based on user preferences
def calculate_relevance_score(entry, user_prefs):
    # Define max possible score for percentage calculation
    max_possible_score = 10.0  # Base max score
    applicable_score = 0.0     # Score that actually applies based on provided preferences
    
    score = 0.0
    score_breakdown = {}
    constraints = []  # Store constraints/feedback
    
    # Debug the incoming preferences
    print(f"Processing destination: {entry['state']}")
    print(f"User preferences: {user_prefs}")
    
    # Region match (strict requirement - if not matching, add to constraints)
    if "region" in user_prefs and user_prefs.get("region") != "Any":
        applicable_score += 3.0
        print(f"Checking region: User wants {user_prefs.get('region')}, destination is in {entry.get('region')}")
        if user_prefs.get("region") == entry.get("region"):
            score += 3.0
            score_breakdown["region_match"] = 3.0
        else:
            score_breakdown["region_match"] = 0.0
            constraints.append({
                "type": "region",
                "message": f"This destination is in {entry.get('region')} India, not {user_prefs.get('region')} India"
            })
    else:
        score_breakdown["region_match"] = "Not specified"
    
    # Month suitability (2 points)
    if "preferred_month" in user_prefs and user_prefs.get("preferred_month") is not None:
        applicable_score += 2.0
        month_num = month_to_number(user_prefs.get("preferred_month"))
        print(f"Checking month: User wants {user_prefs.get('preferred_month')} (num: {month_num}), best time is {entry.get('best_time', '')}")
        if is_suitable_for_month(entry.get("best_time", ""), month_num):
            score += 2.0
            score_breakdown["month_match"] = 2.0
        else:
            score_breakdown["month_match"] = 0.0
            constraints.append({
                "type": "month",
                "message": f"{user_prefs.get('preferred_month')} is not ideal for visiting {entry['state']}. Best time is {entry.get('best_time', 'unknown')}"
            })
    
    # Interest match (up to 3 points, 0.5 per interest match)
    if "interests" in user_prefs and user_prefs.get("interests"):
        user_interests = [interest.lower() for interest in user_prefs.get("interests", [])]
        entry_types = [t.lower() for t in entry.get("types", [])]
        
        print(f"Checking interests: User wants {user_interests}, destination offers {entry_types}")
        
        # Interest weight based on number of interests (max 3 points total)
        interest_weight = min(3.0 / max(len(user_interests), 1), 0.5)
        applicable_score += min(len(user_interests) * interest_weight, 3.0)
        
        # Map user interests to keywords in dataset types
        interest_keywords = {
            "adventure & sports": ["adventure", "wildlife", "trekking"],
            "relaxation & wellness": ["relaxation", "nature", "beach"],
            "temples & divine": ["religious", "spiritual", "temple"],
            "ancient sites": ["historical", "heritage", "history"],
            "culture": ["culture", "tribal", "heritage"],
            "trekking": ["adventure", "nature", "trekking"],
            "beaches": ["beach"]
        }
        
        # Calculate interest match score
        interest_score = 0.0
        matched_interests = []
        unmatched_interests = []
        
        for interest in user_interests:
            keywords = interest_keywords.get(interest.lower(), [interest.lower()])
            match_found = any(keyword in " ".join(entry_types).lower() for keyword in keywords)
            
            print(f"  - Interest '{interest}' has keywords {keywords}, match found: {match_found}")
            
            if match_found:
                interest_score += interest_weight
                matched_interests.append(interest)
            else:
                unmatched_interests.append(interest)
        
        score += interest_score
        score_breakdown["interest_match"] = interest_score
        score_breakdown["matched_interests"] = matched_interests
        score_breakdown["unmatched_interests"] = unmatched_interests
        
        if unmatched_interests:
            constraints.append({
                "type": "interests",
                "message": f"{entry['state']} doesn't offer these interests: {', '.join(unmatched_interests)}"
            })
    
    # Budget considerations (2 points)
    # This is a placeholder as actual budget data is not in the dataset
    if "budget" in user_prefs and user_prefs.get("budget") > 0:
        applicable_score += 2.0
        # Placeholder logic - assume all destinations fit within budget for now
        score += 2.0
        score_breakdown["budget_match"] = 2.0
    
    # Calculate match percentage
    match_percentage = (score / max(applicable_score, 1)) * 100 if applicable_score > 0 else 0
    
    print(f"Final score for {entry['state']}: {score}/{applicable_score} = {match_percentage}%")
    
    return {
        "score": score,
        "max_score": applicable_score,
        "match_percentage": round(match_percentage, 1),
        "score_breakdown": score_breakdown,
        "constraints": constraints
    }
# Function to calculate distance between states
def get_distance(source, destination):
    """Calculate approximate distance between states based on geographical coordinates"""
    # If source and destination are the same
    if source == destination:
        return 0
    
    # If we have both coordinates, calculate distance using Haversine formula
    if source in COORDINATES and destination in COORDINATES:
        from math import radians, sin, cos, sqrt, atan2
        
        # Extract coordinates
        lat1, lon1 = COORDINATES[source]
        lat2, lon2 = COORDINATES[destination]
        
        # Convert to radians
        lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
        
        # Haversine formula
        dlon = lon2 - lon1
        dlat = lat2 - lat1
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * atan2(sqrt(a), sqrt(1-a))
        radius_of_earth = 6371  # Earth's radius in km
        distance = radius_of_earth * c
        
        # Add some randomness to make it more realistic (road distances vs. straight line)
        road_factor = random.uniform(1.2, 1.5)  # Roads are typically 20-50% longer than straight lines
        
        return int(distance * road_factor)
    
    # If we don't have coordinates, return a reasonable default
    return 1200  # Average distance across India

# Calculate travel costs based on mode and distance
def calculate_travel_cost(travel_mode, distance, dest_modifier):
    base_costs = {
        "flight": 2.5,  # ₹2.5 per km for flight
        "train": 1.2,   # ₹1.2 per km for train
        "bus": 0.8,     # ₹0.8 per km for bus
        "cab": 10       # ₹10 per km for cab
    }
    
    # Base calculation
    base_cost = distance * base_costs.get(travel_mode, 1.5)
    
    # Apply modifiers
    if travel_mode == "flight":
        # Flights have base charges and are less affected by distance
        base_cost = 2000 + (distance * 1.8)
        # Short flights are relatively more expensive per km
        if distance < 500:
            base_cost *= 1.3
    elif travel_mode == "train":
        # Trains have tiers - assuming mid-tier
        base_cost = 500 + (distance * 0.8)
    elif travel_mode == "bus":
        # Buses vary by type (assuming semi-deluxe)
        base_cost = 300 + (distance * 0.6)
    elif travel_mode == "cab":
        # Cabs are expensive for long distances
        base_cost = 1000 + (distance * 12)
        # Long distance cabs are slightly cheaper per km
        if distance > 300:
            base_cost = 1000 + (300 * 12) + ((distance - 300) * 10)
    
    # Apply destination cost modifier
    base_cost *= dest_modifier
    
    # Round to nearest 100
    return round(base_cost / 100) * 100

# Calculate food costs
def calculate_food_cost(food_option, days, dest_modifier):
    daily_costs = {
        "budget": 400,      # ₹400 per day for budget eating
        "mid-range": 800,   # ₹800 per day for mid-range dining
        "luxury": 2000,     # ₹2000 per day for luxury dining
        "mix": 1000         # ₹1000 per day for mixed dining options
    }
    
    # Get the base daily cost
    daily_cost = daily_costs.get(food_option, 800)
    
    # Apply destination modifier
    daily_cost *= dest_modifier
    
    # Calculate total for the trip
    total_cost = daily_cost * days
    
    # Round to nearest 100
    return round(total_cost / 100) * 100

# Calculate accommodation costs
def calculate_accommodation_cost(hotel_option, nights, dest_modifier):
    nightly_costs = {
        "budget": 800,       # ₹800 per night for budget stays
        "mid-range": 2000,   # ₹2000 per night for mid-range hotels
        "luxury": 5000,      # ₹5000 per night for luxury hotels
        "homestay": 1200     # ₹1200 per night for homestays/guesthouses
    }
    
    # Get the base nightly cost
    nightly_cost = nightly_costs.get(hotel_option, 2000)
    
    # Apply destination modifier
    nightly_cost *= dest_modifier
    
    # Calculate total for the stay
    total_cost = nightly_cost * nights
    
    # Round to nearest 100
    return round(total_cost / 100) * 100

# Calculate local transport costs
def calculate_local_transport(days, dest_modifier):
    # Average daily cost for local transport
    daily_cost = 250 * dest_modifier
    
    # Total for the trip
    total_cost = daily_cost * days
    
    # Round to nearest 50
    return round(total_cost / 50) * 50

# Calculate sightseeing and activities costs
def calculate_sightseeing(days, dest_modifier):
    # Average daily cost for sightseeing and activities
    daily_cost = 400 * dest_modifier
    
    # Not every day is full sightseeing
    effective_days = max(1, days - 0.5)
    
    # Total for the trip
    total_cost = daily_cost * effective_days
    
    # Round to nearest 50
    return round(total_cost / 50) * 50

# Calculate miscellaneous costs
def calculate_miscellaneous(days, total_budget):
    # Miscellaneous is roughly 5-8% of total budget
    misc_cost = total_budget * random.uniform(0.05, 0.08)
    
    # Round to nearest 50
    return round(misc_cost / 50) * 50

@app.route("/recommend", methods=["POST"])
def recommend():
    user_input = request.json
    print("Received request:", user_input)

    preferred_month = user_input.get("preferred_month")
    region = user_input.get("region")
    interests = user_input.get("interests", [])
    budget = user_input.get("budget", 0)
    crowd_preference = user_input.get("crowd_preference")
    travel_style = user_input.get("travel_style")
    
    # Score all destinations based on relevance to user preferences
    scored_destinations = []
    for entry in tourism_data:
        relevance_data = calculate_relevance_score(entry, user_input)
        entry_with_score = entry.copy()
        entry_with_score.update(relevance_data)
        
        # Add the preferred month for display
        if preferred_month:
            month_num = month_to_number(preferred_month)
            entry_with_score["best_months"] = [month_num]
        
        scored_destinations.append(entry_with_score)
    
    # Filter strictly by region if specified
    region_filtered = scored_destinations
    if region and region != "Any":
        region_filtered = [dest for dest in scored_destinations if dest.get("region") == region]
        
        # If no destinations in the specified region, include feedback
        if not region_filtered:
            # Sort all destinations by match percentage for best alternatives
            scored_destinations.sort(key=lambda x: x["match_percentage"], reverse=True)
            top_alternatives = scored_destinations[:3]
            
            # Find best alternative regions based on interests
            alternative_regions = {}
            for dest in top_alternatives:
                r = dest.get("region")
                if r not in alternative_regions:
                    alternative_regions[r] = 1
                else:
                    alternative_regions[r] += 1
            
            best_regions = [r for r, count in alternative_regions.items()]
            
            response = {
                "recommendations": top_alternatives,
                "feedback": {
                    "no_region_match": True,
                    "message": f"No destinations found in {region} India that match your criteria.",
                    "suggestions": [
                        f"Try selecting one of these regions instead: {', '.join(best_regions)}",
                        "Or select 'Any' for region to see more options"
                    ]
                }
            }
            return jsonify(response)
    
    # Sort by match percentage, descending
    region_filtered.sort(key=lambda x: x["match_percentage"], reverse=True)
    
    # Print debug info for top matches
    print("\nTop 3 matches after filtering and sorting:")
    for i, dest in enumerate(region_filtered[:3]):
        print(f"{i+1}. {dest['state']} - {dest['match_percentage']}%")
        print(f"   Score breakdown: {dest['score_breakdown']}")
        print(f"   Constraints: {dest['constraints']}")
    
    # Check if there are any good matches (>=50%)
    good_matches = [dest for dest in region_filtered if dest["match_percentage"] >= 50]
    
    # Collect all constraints from top results
    all_constraints = []
    for dest in region_filtered[:5]:
        all_constraints.extend(dest.get("constraints", []))
    
    # Generate targeted feedback using the function
    feedback = generate_targeted_feedback(user_input, all_constraints, region_filtered)
    
    # Take top recommendations (minimum 3, maximum 10)
    if good_matches:
        recommendations = good_matches[:min(10, len(good_matches))]
    else:
        recommendations = region_filtered[:min(3, len(region_filtered))]
    
    # Format for response
    formatted_recommendations = []
    for rec in recommendations:
        formatted_recommendations.append({
            "state": rec["state"],
            "region": rec.get("region", "All India"),
            "famous_places": rec.get("famous_places", []),
            "hidden_gems": rec.get("hidden_gems", []), 
            "best_time": rec.get("best_time", ""),
            "types": rec.get("types", []),
            "match_percentage": rec.get("match_percentage", 0),
            "score_breakdown": rec.get("score_breakdown", {}),
            "constraints": rec.get("constraints", []),
            "best_months": rec.get("best_months", [])
        })

    response_data = {
        "recommendations": formatted_recommendations,
        "feedback": feedback
    }
    
    return jsonify(response_data)
@app.route("/budget-summary", methods=["POST"])
def budget_summary():
    data = request.json
    source_state = data.get("sourceState")
    destination_state = data.get("destinationState")
    travel_mode = data.get("travel")
    food_option = data.get("food")
    hotel_option = data.get("hotel")
    nights = int(data.get("nights", 1))
    days = nights + 1  # Usually one more day than nights
    
    # Validate inputs
    if not source_state or not destination_state:
        return jsonify({"error": "Source and destination states are required"}), 400
    
    # Get distance between states
    distance = get_distance(source_state, destination_state)
    
    # Get destination cost modifier
    dest_modifier = STATE_COST_MODIFIERS.get(destination_state, 1.0)
    
    # Calculate costs for each category
    travel_cost = calculate_travel_cost(travel_mode, distance, dest_modifier)
    food_cost = calculate_food_cost(food_option, days, dest_modifier)
    hotel_cost = calculate_accommodation_cost(hotel_option, nights, dest_modifier)
    local_transport = calculate_local_transport(days, dest_modifier)
    sightseeing = calculate_sightseeing(days, dest_modifier)
    
    # Calculate subtotal
    subtotal = travel_cost + food_cost + hotel_cost + local_transport + sightseeing
    
    # Calculate miscellaneous costs
    misc_cost = calculate_miscellaneous(days, subtotal)
    
    # Total budget
    total_budget = subtotal + misc_cost
    
    # Get recommended tourism places for the destination
    recommended_places = []
    if destination_state in TOURISM_PLACES:
        # Select 3-5 random places from the destination's list
        places = TOURISM_PLACES[destination_state]
        num_recommendations = min(len(places), random.randint(3, 5))
        recommended_places = random.sample(places, num_recommendations)
    
    # Travel tips based on destination
    travel_tips = [
        f"The best time to visit {destination_state} is typically during winter months.",
        f"Local transport in {destination_state} might require advance booking during peak seasons.",
        "Carry sufficient cash, as some remote areas might have limited ATM facilities."
    ]
    
    if destination_state in ["Ladakh", "Himachal Pradesh", "Sikkim", "Arunachal Pradesh", "Uttarakhand"]:
        travel_tips.append("Prepare for altitude sickness if traveling to high-altitude areas.")
    
    if destination_state in ["Goa", "Kerala", "Andaman and Nicobar Islands", "Puducherry", "Lakshadweep"]:
        travel_tips.append("Don't forget to pack swimwear and sunscreen for beach destinations.")
    
    # Prepare the response
    response = {
        "source_state": source_state,
        "destination_state": destination_state,
        "distance": distance,
        "travel_option": travel_mode,
        "food_option": food_option,
        "hotel_option": hotel_option,
        "days": days,
        "nights": nights,
        "estimated_budget": total_budget,
        "breakdown": {
            "Travel": travel_cost,
            f"Food (for {days} days)": food_cost,
            f"Accommodation (for {nights} nights)": hotel_cost,
            "Local Transport": local_transport,
            "Sightseeing & Activities": sightseeing,
            "Miscellaneous": misc_cost
        },
        "recommended_places": recommended_places,
        "travel_tips": travel_tips
    }
    
    return jsonify(response)
@app.route('/<path:path>')
def serve_file(path):
    return send_from_directory('.', path)
if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0')