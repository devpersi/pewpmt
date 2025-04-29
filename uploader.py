import json
import requests
import time

# Path to your JSON file with posts
json_file = "wordpress_posts.json"

# WordPress API URL (old website)
old_media_base_url = "https://targetsite.com/wp-json/wp/v2/media/"

# Target WordPress API URL (new website)
target_base_url = "https://targetsite.com/wp-json/wp/v2/posts"
new_media_base_url = "https://targetsite.com/wp-json/wp/v2/media"

# WARNING WordPress credentials: 
# If you generate an app password, remember to use it under your real username, not the app's name, or you'll get an auth error
target_username = 'username' # os.getenv('WP_USERNAME') # Update with your WordPress username 
target_password = 'password' # os.getenv('WP_APP_PASSWORD') # Update with your WordPress app password

# Encode credentials for Basic Authentication
target_auth = (target_username, target_password)

# Load posts from the JSON file
try:
    with open(json_file, "r", encoding="utf-8") as file:
        all_posts = json.load(file)
        print(f"Loaded {len(all_posts)} posts from {json_file}.")
except FileNotFoundError:
    print(f"Error: JSON file '{json_file}' not found.")
    exit(1)
except json.JSONDecodeError:
    print(f"Error: Failed to decode JSON file '{json_file}'.")
    exit(1)

# Function to upload featured image and return its ID
def upload_image(image_url_by_id):
    try:
        # Download the image
        image_response = requests.get(image_url_by_id)
        if image_response.status_code != 200:
            print(f"Failed to get image link: {image_url_by_id}")
            return None
        
        image_url = json.loads(image_response.content.decode('utf-8'))['guid']['rendered']
        
        # Optional: Add a delay to avoid hitting rate limits
        time.sleep(1)
        
        image = requests.get(image_url)
        if image.status_code != 200:
            print(f"Failed to download image: {image_url}")
            return None
        
        filename = image_url.split("/")[-1]
        headers = {
            "Content-Disposition": f"attachment; filename={filename}",
            "Content-Type": "image/jpeg"
        }
        
        # Upload the image to the target WordPress site
        post_response = requests.post(
            new_media_base_url, data=image.content, auth=target_auth, headers=headers
        )

        if post_response.status_code == 201:
            print(f"Successfully uploaded image: {image_url_by_id}")
            return post_response.json()["id"]  # Return the new image ID
        else:
            print(f"Failed to upload image: {post_response.status_code} - {post_response.text}")
            return None

    except Exception as e:
        print(f"Error during image upload: {e}")
        return None

# Upload posts to the target website
for idx, post in enumerate(all_posts, start=1):
    # Upload the featured image if it exists
    image_id = None
    if post.get("featured_media"):
        image_url = old_media_base_url + str(post["featured_media"])
        image_id = upload_image(image_url)
    
    # Prepare data for the new post
    new_post_data = {
        "title": post.get("title", {}).get("rendered", "Untitled"), # Post title
        "content": post.get("content", {}).get("rendered", ""), # Post text content
        "featured_media": image_id if image_id else None, # Post image
        
        #"excerpt": post.get("excerpt", {}).get("rendered", ""),
        #"status": post.get("status", "draft"),
        #"date": post.get("date", "2024-11-30T08:44:23"),
        #"slug": post.get("slug", f"untitled{idx}"),
        #"categories": [20]
        # https://developer.wordpress.org/rest-api/reference/posts/
    }

    # Handle featured image
    featured_image_url = post.get("featured_image")
    if featured_image_url:
        image_id = upload_image(featured_image_url)
        if image_id:
            new_post_data["_thumbnail_id"] = image_id
        else:
            print(f"Failed to upload featured image for post {idx}")

    # Post to the target WordPress site
    response = requests.post(target_base_url, json=new_post_data, auth=target_auth)

    if response.status_code == 201:
        print(f"Successfully uploaded post {idx}: {new_post_data['title']}")
    elif response.status_code == 403:
        print(f"Failed to upload post {idx}: Forbidden (403). Check your API credentials.")
    elif response.status_code == 404:
        print(f"Failed to upload post {idx}: Not Found (404). Check your API URL.")
    else:
        print(f"Failed to upload post {idx}: {response.status_code} - {response.text}")

    # Optional: Add a delay to avoid hitting rate limits
    time.sleep(1)

print("All posts processed.")
