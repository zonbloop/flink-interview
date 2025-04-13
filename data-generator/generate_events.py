#!/usr/bin/env python3

import json
import os
import random
import time
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional

from kafka import KafkaProducer

# Configuration from environment variables
KAFKA_BROKER = os.environ.get("KAFKA_BROKER", "kafka:9092")
IMPRESSION_TOPIC = os.environ.get("IMPRESSION_TOPIC", "ad-impressions")
CLICK_TOPIC = os.environ.get("CLICK_TOPIC", "ad-clicks")
EVENT_RATE = int(os.environ.get("EVENT_RATE", "50"))  # Events per second
CLICK_RATIO = float(os.environ.get("CLICK_RATIO", "0.1"))  # % of impressions that get clicked

# Sample data for generation
CAMPAIGNS = [f"camp-{i}" for i in range(1, 11)]
ADS = [f"ad-{i}" for i in range(1, 101)]
DEVICE_TYPES = ["mobile", "desktop", "tablet"]
BROWSERS = ["chrome", "safari", "firefox", "edge"]
USER_POOL_SIZE = 10000

# Store impressions temporarily to generate clicks
impression_buffer: List[Dict[str, Any]] = []
MAX_BUFFER_SIZE = 1000

def create_kafka_producer() -> KafkaProducer:
    """Creates and returns a Kafka producer"""
    return KafkaProducer(
        bootstrap_servers=KAFKA_BROKER,
        value_serializer=lambda v: json.dumps(v).encode('utf-8'),
        key_serializer=lambda v: v.encode('utf-8') if v else None
    )

def generate_impression() -> Dict[str, Any]:
    """Generates a random ad impression event"""
    user_id = f"user-{random.randint(1, USER_POOL_SIZE)}"
    campaign_id = random.choice(CAMPAIGNS)
    ad_id = random.choice(ADS)
    device_type = random.choice(DEVICE_TYPES)
    browser = random.choice(BROWSERS)
    cost = round(random.uniform(0.01, 0.5), 2)
    timestamp = int(datetime.now().timestamp() * 1000)  # milliseconds
    
    return {
        "impression_id": str(uuid.uuid4()),
        "user_id": user_id,
        "campaign_id": campaign_id,
        "ad_id": ad_id,
        "device_type": device_type,
        "browser": browser,
        "event_timestamp": timestamp,  
        "cost": cost
    }

def generate_click(impression: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Generates a click event based on an impression"""
    # Determine if this impression gets clicked based on CLICK_RATIO
    if random.random() > CLICK_RATIO:
        return None
    
    # Add a realistic delay (0-10 seconds)
    click_delay = random.randint(0, 10000)  # milliseconds
    
    return {
        "click_id": str(uuid.uuid4()),
        "impression_id": impression["impression_id"],
        "user_id": impression["user_id"],
        "event_timestamp": impression["event_timestamp"] + click_delay
    }

def main():
    """Main loop to generate and send events"""
    producer = create_kafka_producer()
    
    # Wait for Kafka to be ready
    print("Waiting for Kafka to be ready...")
    time.sleep(10)
    print("Starting event generation...")
    
    # Introduce campaign-specific click behavior
    campaign_click_boost = {}
    for campaign in CAMPAIGNS:
        # Some campaigns perform better than others
        campaign_click_boost[campaign] = random.uniform(0.8, 1.5)
    
    # Every 10 minutes, change the campaign performance to simulate time patterns
    last_behavior_change = time.time()
    
    try:
        while True:
            # Generate impression
            impression = generate_impression()
            
            # Apply campaign-specific boost to click probability
            actual_click_ratio = min(1.0, CLICK_RATIO * campaign_click_boost[impression["campaign_id"]])
            
            # Send impression to Kafka
            producer.send(IMPRESSION_TOPIC, key=impression["impression_id"], value=impression)
            
            # Maybe generate click with adjusted probability
            if random.random() < actual_click_ratio:
                # Add a realistic delay (0-10 seconds)
                click_delay = random.randint(500, 10000)  # milliseconds
                click = {
                    "click_id": str(uuid.uuid4()),
                    "impression_id": impression["impression_id"],
                    "user_id": impression["user_id"],
                    "event_timestamp": impression["event_timestamp"] + click_delay 
                }
                # Send click to Kafka after delay
                time.sleep(click_delay / 1000)  # Convert to seconds
                producer.send(CLICK_TOPIC, key=click["click_id"], value=click)
            
            # Check if we need to update campaign behavior
            current_time = time.time()
            if current_time - last_behavior_change > 600:  # 10 minutes
                print("Updating campaign performance...")
                for campaign in CAMPAIGNS:
                    # Randomly adjust campaign performance
                    campaign_click_boost[campaign] = random.uniform(0.8, 1.5)
                last_behavior_change = current_time
                
                # Introduce an anomaly for one random campaign
                anomaly_campaign = random.choice(CAMPAIGNS)
                if random.random() < 0.5:
                    # Sudden increase in CTR
                    campaign_click_boost[anomaly_campaign] = random.uniform(2.0, 3.0)
                    print(f"Anomaly: High CTR for {anomaly_campaign}")
                else:
                    # Sudden decrease in CTR
                    campaign_click_boost[anomaly_campaign] = random.uniform(0.1, 0.3)
                    print(f"Anomaly: Low CTR for {anomaly_campaign}")
            
            # Control generation rate
            wait_time = 1.0 / EVENT_RATE
            time.sleep(wait_time)
            
    except KeyboardInterrupt:
        print("Shutting down event generator...")
    finally:
        producer.flush()
        producer.close()

if __name__ == "__main__":
    main()