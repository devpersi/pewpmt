import requests
import time
import json

# WordPress API URL
base_url = "https://targetsite.com/wp-json/wp/v2/posts"
# for free wordpress sites
# base_url = "https://public-api.wordpress.com/wp/v2/sites/targetsite.wordpress.com/posts"
per_page = 8
all_posts = []
page = 1

# JSON file to save the data
json_file = "wordpress_posts.json"

with requests.Session() as session:
    while True:
        url = f"{base_url}?per_page={per_page}&page={page}"
        response = session.get(url)
        
        if response.status_code != 200:
            print(f"Error fetching posts: {response.status_code}")
            break
        
        posts = response.json()
        if not posts:
            break
        
        all_posts.extend(posts)
        print(f"Retrieved page {page}, {len(posts)} posts")
        
        page += 1
        
        # Throttle requests to avoid being blocked: wait 2 seconds between each request
        time.sleep(2)

# Save data to a JSON file
with open(json_file, "w", encoding="utf-8") as f:
    json.dump(all_posts, f, ensure_ascii=False, indent=4)

print(f"Total posts retrieved: {len(all_posts)}")
print(f"Data saved to {json_file}")
