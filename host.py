import streamlit as st
import re
import time
import requests
from urllib.parse import quote
import json

# Set page config
st.set_page_config(
    page_title="AI Shopping Agent",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Groq API configuration - Replace with your actual key
GROQ_API_KEY = "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"  # Replace with your Groq API key
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"

# Initialize session state
if 'products' not in st.session_state:
    st.session_state.products = []
if 'query' not in st.session_state:
    st.session_state.query = ""
if 'quick_search' not in st.session_state:
    st.session_state.quick_search = None

# -------- Utility Functions (kept for context, not used for live scraping) --------
def extract_price(price_text):
    """Extracts the most likely selling price (float) from text."""
    if not price_text:
        return None
    
    text = price_text.replace(',', '').replace(' ', '')
    all_rupee_prices = re.findall(r'₹(\d+\.?\d*)', text)
    if all_rupee_prices:
        try:
            return float(all_rupee_prices[-1])
        except ValueError:
            pass

    all_prices = re.findall(r'(\d+\.?\d*)', text)
    for price_str in reversed(all_prices):
        try:
            price = float(price_str)
            if 1 <= price <= 10000:
                return price
        except:
            continue
    return None

def clean_product_name(name):
    """Clean product name by removing common cruft."""
    if not name:
        return ""
    
    patterns_to_remove = [
        r'^MINS\s+',
        r'\d+\.?\d*\s*[★☆⭑]',
        r'\d+\s*Ratings?',
        r'(?:ADD|OFF|Out\s+of\s+Stock|\d+\s+mins)\s*',
        r'\s*\|.*$',
        r'\.{3,}',
        r'\s+'
    ]
    
    for pattern in patterns_to_remove:
        name = re.sub(pattern, ' ', name, flags=re.IGNORECASE)
    
    return name.strip()

def extract_quantity(name):
    """Extract quantity from product name."""
    patterns = [
        r'(\d+\s*(?:litre|liter|ltr|L|ml|g|kg|pcs|units|pack|gm|mg|oz))',
        r'(\d+\s*[mM][lL])',
        r'(\d+\s*[gG])',
        r'(\d+\s*[kK][gG])',
        r'(\d+\s*[mM][gG])'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, name, re.IGNORECASE)
        if match:
            return match.group(1).strip()
    return ""

# -------- Mock Data with RELIABLE SEARCH LINKS (BigBasket updated) --------
def scrape_bigbasket(search_query):
    """Simulate BigBasket scraping using generic search links for reliability."""
    products = []
    
    # ALWAYS use the generic search link for BigBasket to maximize reliability
    search_link = f"https://www.bigbasket.com/ps/?q={quote(search_query)}" 

    # Mock product data 
    mock_data = {
        "milk": [
            {"name": "Amul Taaza Homogenised Toned Milk 500 ml", "price": 32.0, "quantity": "500 ml"},
            {"name": "Amul Gold Full Cream Milk 1 L", "price": 60.0, "quantity": "1 L"},
            {"name": "Nestle Everyday Dairy Whitener 200 g", "price": 85.0, "quantity": "200 g"},
        ],
        "bread": [
            {"name": "Britannia Whole Wheat Bread 400 g", "price": 45.0, "quantity": "400 g"},
            {"name": "Modern Sandwich Bread 400 g", "price": 35.0, "quantity": "400 g"},
            {"name": "Harvest Whole Wheat Bread 400 g", "price": 42.0, "quantity": "400 g"},
        ],
        "eggs": [
            {"name": "Fresh Farm Eggs 6 pcs", "price": 60.0, "quantity": "6 pcs"},
            {"name": "Organic Brown Eggs 6 pcs", "price": 90.0, "quantity": "6 pcs"},
            {"name": "Country Eggs 12 pcs", "price": 110.0, "quantity": "12 pcs"},
        ],
        "rice": [
            {"name": "Fortune Basmati Rice 1 kg", "price": 120.0, "quantity": "1 kg"},
            {"name": "India Gate Classic Basmati Rice 1 kg", "price": 150.0, "quantity": "1 kg"},
            {"name": "Daawat Rozana Gold Rice 5 kg", "price": 450.0, "quantity": "5 kg"},
        ],
        "chips": [
            {"name": "Lays India's Magic Masala Potato Chips 52 g", "price": 30.0, "quantity": "52 g"},
            {"name": "Kurkure Masala Munch Chips 60 g", "price": 25.0, "quantity": "60 g"},
            {"name": "Bingo Mad Angles Chips 60 g", "price": 20.0, "quantity": "60 g"},
        ],
        "chocolate": [
            {"name": "Cadbury Dairy Milk Chocolate 150 g", "price": 180.0, "quantity": "150 g"},
            {"name": "Nestle KitKat Chocolate 4 Fingers", "price": 50.0, "quantity": "41 g"},
        ],
        "coffee": [
            {"name": "Nescafe Classic Coffee 50 g", "price": 120.0, "quantity": "50 g"},
            {"name": "Bru Gold Instant Coffee 100 g", "price": 200.0, "quantity": "100 g"},
        ],
        "tea": [
            {"name": "Taj Mahal Tea 500 g", "price": 250.0, "quantity": "500 g"},
            {"name": "Red Label Tea 500 g", "price": 220.0, "quantity": "500 g"},
        ]
    }
    
    # Get products for the search query
    search_products = mock_data.get(search_query.lower(), [])
    
    # If no specific products found, show generic results
    if not search_products:
        search_products = [
            {"name": f"Premium {search_query.title()} 500 g", "price": 99.0, "quantity": "500 g"},
            {"name": f"Standard {search_query.title()} 1 kg", "price": 149.0, "quantity": "1 kg"},
            {"name": f"Economy {search_query.title()} Pack", "price": 49.0, "quantity": "250 g"},
        ]
    
    for product in search_products:
        products.append({
            "source": "BigBasket",
            "name": product["name"],
            "price": product["price"],
            "quantity": product["quantity"],
            "link": search_link, # NOW ALWAYS USING THE RELIABLE SEARCH LINK
            "quality_score": 4 if any(brand in product["name"].lower() for brand in ['amul', 'nestle', 'britannia', 'tata', 'fortune', 'cadbury', 'nescafe']) else 3
        })
    
    return products

def scrape_blinkit(query):
    """Simulate Blinkit scraping using generic search links for reliability."""
    products = []
    
    # ALWAYS use the generic search link for Blinkit
    search_link = f"https://blinkit.com/s/?q={quote(query)}"
    
    # Mock product data
    mock_data = {
        "milk": [
            {"name": "Amul Gold Full Cream Milk 500 ml", "price": 35.0, "quantity": "500 ml"},
            {"name": "Amul Taaza Toned Milk 1 L", "price": 62.0, "quantity": "1 L"},
            {"name": "Mother Dairy Toned Milk 500 ml", "price": 32.0, "quantity": "500 ml"},
        ],
        "bread": [
            {"name": "Britannia Fruit Bread 400 g", "price": 48.0, "quantity": "400 g"},
            {"name": "Harvest Whole Wheat Bread 400 g", "price": 38.0, "quantity": "400 g"},
            {"name": "Modern Sandwich Bread 400 g", "price": 36.0, "quantity": "400 g"},
        ],
        "eggs": [
            {"name": "Fresh Country Eggs 6 pcs", "price": 55.0, "quantity": "6 pcs"},
            {"name": "Farm Fresh Eggs 12 pcs", "price": 100.0, "quantity": "12 pcs"},
            {"name": "Organic Brown Eggs 6 pcs", "price": 85.0, "quantity": "6 pcs"},
        ],
        "rice": [
            {"name": "Fortune Rice Bran Health Oil 1 L", "price": 155.0, "quantity": "1 L"},
            {"name": "Tata Sampann Unpolished Toor Dal 500 g", "price": 95.0, "quantity": "500 g"},
            {"name": "India Gate Basmati Rice 1 kg", "price": 145.0, "quantity": "1 kg"},
        ],
        "chips": [
            {"name": "Kurkure Masala Munch Chips 60 g", "price": 25.0, "quantity": "60 g"},
            {"name": "Bingo Mad Angles Chips 60 g", "price": 20.0, "quantity": "60 g"},
            {"name": "Lays Potato Chips 52 g", "price": 30.0, "quantity": "52 g"},
        ],
        "chocolate": [
            {"name": "Cadbury Dairy Milk Silk Chocolate 60 g", "price": 80.0, "quantity": "60 g"},
            {"name": "Nestle Munch Chocolate 30 g", "price": 20.0, "quantity": "30 g"},
        ],
        "coffee": [
            {"name": "Nescafe Sunrise Coffee 100 g", "price": 150.0, "quantity": "100 g"},
            {"name": "Bru Instant Coffee 50 g", "price": 90.0, "quantity": "50 g"},
        ],
        "tea": [
            {"name": "Tata Tea Gold 500 g", "price": 240.0, "quantity": "500 g"},
            {"name": "Brooke Bond Red Label Tea 250 g", "price": 120.0, "quantity": "250 g"},
        ]
    }
    
    # Get products for the search query
    search_products = mock_data.get(query.lower(), [])
    
    # If no specific products found, show generic results
    if not search_products:
        search_products = [
            {"name": f"Express {query.title()} 500 g", "price": 89.0, "quantity": "500 g"},
            {"name": f"Quick {query.title()} Pack", "price": 129.0, "quantity": "750 g"},
            {"name": f"Premium {query.title()} 1 kg", "price": 199.0, "quantity": "1 kg"},
        ]
    
    for product in search_products:
        products.append({
            "source": "Blinkit",
            "name": product["name"],
            "price": product["price"],
            "quantity": product["quantity"],
            "link": search_link, # Using the dynamic search URL
            "quality_score": 4 if any(brand in product["name"].lower() for brand in ['amul', 'britannia', 'tata', 'fortune', 'cadbury', 'nescafe']) else 3
        })
    
    return products

# -------- Groq AI Analysis --------
def analyze_products_with_ai(products, query):
    """Use Groq AI to analyze and recommend products."""
    if not products:
        return "No products found to analyze."
    
    try:
        # Prepare product information
        product_info = "\n".join([
            f"{i+1}. {p['name']} - ₹{p['price']} ({p['source']}) - {p.get('quantity', 'N/A')}"
            for i, p in enumerate(products[:8])
        ])
        
        prompt = f"""
        Analyze these shopping products for "{query}" and provide shopping advice:
        
        {product_info}
        
        Give:
        1. Best deal summary with specific product recommendations
        2. Price comparisons between different stores
        3. Specific recommendation on which product to buy and why
        4. Quality observations based on brands and prices
        5. Final practical shopping advice
        
        Keep it practical and helpful. Use emojis and be specific about product names.
        """
        
        headers = {
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json"
        }
        
        data = {
            "messages": [{"role": "user", "content": prompt}],
            "model": "llama-3.1-8b-instant",
            "max_tokens": 600,
            "temperature": 0.7
        }
        
        response = requests.post(GROQ_API_URL, headers=headers, json=data, timeout=30)
        response.raise_for_status()
        
        result = response.json()
        return result["choices"][0]["message"]["content"]
        
    except Exception as e:
        return f"""🤖 AI Shopping Assistant Analysis:

📊 **Best Deal**: {products[0]['name']} at ₹{products[0]['price']} from {products[0]['source']}

💡 **Smart Shopping Tips**:
• Compare prices per unit (₹ per kg/ml) across stores
• Trusted brands like Amul, Britannia, Nestle offer consistent quality
• Check quantity vs price for best value
• Consider delivery time and freshness for perishable items

🛒 **Recommendation**: {products[0]['name']} offers the best value for money!"""

# -------- Compare & Select Best Products --------
def compare_and_select_best(bb_products, blinkit_products, top_n=8):
    """Select best products based on price and quality"""
    combined = bb_products + blinkit_products
    
    if not combined:
        return []
    
    # Remove duplicates
    unique_products = []
    seen_names = set()
    
    for product in combined:
        # Create a key based on a standardized name root and price for comparison
        simple_name = re.sub(r'[^a-zA-Z0-9]', '', product['name'].lower())[:25]
        key = (simple_name, product['price'])
        
        if key not in seen_names:
            unique_products.append(product)
            seen_names.add(key)
    
    # Sort by price, then quality score
    sorted_products = sorted(unique_products, 
                             key=lambda x: (x['price'], -x.get('quality_score', 0)))
    
    return sorted_products[:top_n]

# -------- Main App --------
def main():
    st.title("🤖 AI Shopping Agent")
    st.markdown("### Smart Price Comparison with AI Analysis")
    
    # Sidebar
    with st.sidebar:
        st.header("⚙️ Search Settings")
        query = st.text_input("🔍 Product to search", value="milk", placeholder="e.g., milk, bread, eggs, chocolate...")
        max_products = st.slider("Products to show", 3, 12, 8)
        enable_ai = st.checkbox("Enable AI Analysis", value=True)
        
        st.markdown("---")
        st.markdown("**🛒 Supported Stores:**")
        st.markdown("• BigBasket")
        st.markdown("• Blinkit")
        
        st.markdown("---")
        st.markdown("**💡 Quick Tips:**")
        st.markdown("• Click any product button below")
        st.markdown("• Reliable store links")
        st.markdown("• AI gives smart recommendations")

    # Enhanced Quick search buttons with more options
    st.markdown("### 🔥 Popular Searches")
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    with col1:
        if st.button("🥛 Milk", use_container_width=True):
            st.session_state.query = "milk"
            st.rerun()
    with col2:
        if st.button("🍞 Bread", use_container_width=True):
            st.session_state.query = "bread"
            st.rerun()
    with col3:
        if st.button("🥚 Eggs", use_container_width=True):
            st.session_state.query = "eggs"
            st.rerun()
    with col4:
        if st.button("🍚 Rice", use_container_width=True):
            st.session_state.query = "rice"
            st.rerun()
    with col5:
        if st.button("🥔 Chips", use_container_width=True):
            st.session_state.query = "chips"
            st.rerun()
    with col6:
        if st.button("🍫 Chocolate", use_container_width=True):
            st.session_state.query = "chocolate"
            st.rerun()

    # Second row of search options
    col7, col8, col9, col10, col11, col12 = st.columns(6)
    with col7:
        if st.button("☕ Coffee", use_container_width=True):
            st.session_state.query = "coffee"
            st.rerun()
    with col8:
        if st.button("🫖 Tea", use_container_width=True):
            st.session_state.query = "tea"
            st.rerun()
    with col9:
        if st.button("🧴 Shampoo", use_container_width=True):
            st.session_state.query = "shampoo"
            st.rerun()
    with col10:
        if st.button("🧼 Soap", use_container_width=True):
            st.session_state.query = "soap"
            st.rerun()
    with col11:
        if st.button("🍪 Biscuits", use_container_width=True):
            st.session_state.query = "biscuits"
            st.rerun()
    with col12:
        if st.button("🥤 Juice", use_container_width=True):
            st.session_state.query = "juice"
            st.rerun()

    # Use session state query if set
    if st.session_state.query:
        query = st.session_state.query

    # Search button
    if st.button("🔍 Search Products", type="primary", use_container_width=True):
        if not query.strip():
            st.warning("⚠️ Please enter a product to search!")
        else:
            with st.spinner("🔄 Searching BigBasket & Blinkit..."):
                # Simulate search delay
                time.sleep(2)
                
                # Get products from both stores
                bb_products = scrape_bigbasket(query)
                blinkit_products = scrape_blinkit(query)
                
                # Combine and select best
                best_products = compare_and_select_best(bb_products, blinkit_products, max_products)
                st.session_state.products = best_products
                st.session_state.query = query

    # Display results
    if st.session_state.products:
        products = st.session_state.products
        query = st.session_state.query
        
        st.markdown(f"## 📊 Results for: **{query.title()}**")
        
        # Statistics
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Products", len(products))
        with col2:
            bb_count = len([p for p in products if p['source'] == 'BigBasket'])
            st.metric("BigBasket", bb_count)
        with col3:
            blinkit_count = len([p for p in products if p['source'] == 'Blinkit'])
            st.metric("Blinkit", blinkit_count)
        
        # Products list
        st.markdown("### 🛍️ Available Products")
        
        # Updated note for users
        st.info("💡 **Link Reliability Note**: Since we are simulating real-time shopping, the links for **both BigBasket and Blinkit** are set to take you to the store's **search results page** for that product (e.g., searching 'milk'). This ensures the links *always work* reliably, even if we can't provide the direct product page link due to local stock limitations.")
        
        for idx, product in enumerate(products, 1):
            with st.container():
                col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
                
                with col1:
                    st.markdown(f"**#{idx} {product['name']}**")
                    if product['quantity']:
                        st.caption(f"📦 {product['quantity']}")
                    st.caption(f"🏪 {product['source']}")
                    
                with col2:
                    st.markdown(f"**₹{product['price']}**")
                    
                with col3:
                    quality = "⭐ Premium" if product['quality_score'] >= 4 else "✅ Standard"
                    st.markdown(quality)
                    
                with col4:
                    # Use markdown to create clickable links that open in new tab
                    st.markdown(f'<a href="{product["link"]}" target="_blank"><button style="background-color: #FF4B4B; color: white; border: none; padding: 0.5rem 1rem; border-radius: 0.5rem; cursor: pointer;">🛒 View Product</button></a>', 
                                unsafe_allow_html=True)
                
                st.markdown("---")
        
        # Best deal
        if products:
            best = products[0]
            st.success(f"🏆 **BEST DEAL**: {best['name']} @ ₹{best['price']} from {best['source']}")
            
            if len(products) > 1:
                most_expensive = max(products, key=lambda x: x['price'])
                savings = most_expensive['price'] - best['price']
                if savings > 0:
                    st.info(f"💰 Save ₹{savings:.2f} compared to the most expensive option!")
        
        # AI Analysis
        if enable_ai:
            st.markdown("## 🤖 AI Shopping Assistant")
            with st.spinner("AI analyzing your products..."):
                ai_analysis = analyze_products_with_ai(products, query)
                st.markdown(ai_analysis)
    
    elif not st.session_state.products and st.session_state.query:
        st.error("❌ No products found. Try a different search term.")
    
    else:
        # Welcome message
        st.markdown("""
        ## 🎯 Welcome to AI Shopping Agent!
        
        **Find the best deals with AI-powered recommendations:**
        
        1. **Click** any product button above
        2. **Or type** your own product in search bar
        3. **Compare** prices across BigBasket & Blinkit
        4. **Get** AI shopping advice
        5. **Click** product links to visit stores
        
        ### 🚀 Features:
        • Reliable store links (takes you to search results)
        • Smart AI recommendations
        • Price comparison across stores
        • Quality scoring based on brands
        
        *Note: All store links now go to the product search results for maximum reliability.*
        """)

# Run the app
if __name__ == "__main__":
    main()