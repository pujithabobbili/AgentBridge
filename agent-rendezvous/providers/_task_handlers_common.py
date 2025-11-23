# Common task handler implementations that can be shared
# Each agent will import and adapt these based on their characteristics

import re
import hashlib
import json
import time


def translate_text_handler(text: str, target_language: str = "Spanish", quality: str = "high") -> dict:
    """Translate text with quality variations."""
    translations_map = {
        "Spanish": {
            "Hello": "Hola",
            "how are you": "cómo estás",
            "today": "hoy",
            "good": "bueno",
            "thank you": "gracias",
            "good morning": "buenos días",
            "good night": "buenas noches"
        },
        "French": {
            "Hello": "Bonjour",
            "how are you": "comment allez-vous",
            "today": "aujourd'hui"
        }
    }
    
    translated = text
    if target_language in translations_map:
        for en, target in translations_map[target_language].items():
            translated = re.sub(r'\b' + re.escape(en) + r'\b', target, translated, flags=re.IGNORECASE)
    
    if translated == text:
        if target_language == "Spanish":
            translated = f"[ES] {text}"
        elif target_language == "French":
            translated = f"[FR] {text}"
        else:
            translated = f"[{target_language}] {text}"
    
    return {
        "original_text": text,
        "translated_text": translated,
        "target_language": target_language,
        "source_language": "English"
    }


def analyze_sentiment_handler(text: str, quality: str = "high") -> dict:
    """Analyze sentiment with quality variations."""
    positive_words = ['love', 'loved', 'amazing', 'great', 'excellent', 'wonderful', 'fantastic', 'outstanding', 'exceptional', 'highly', 'recommended', 'best', 'good', 'awesome', 'brilliant']
    negative_words = ['hate', 'hated', 'terrible', 'awful', 'bad', 'worst', 'disappointed', 'poor', 'horrible', 'disgusting', 'annoying']
    
    text_lower = text.lower()
    positive_count = sum(1 for word in positive_words if word in text_lower)
    negative_count = sum(1 for word in negative_words if word in text_lower)
    
    if positive_count > negative_count:
        sentiment = "positive"
        base_confidence = 0.85 if quality == "high" else 0.70
        confidence = min(0.95, base_confidence + (positive_count * 0.03))
    elif negative_count > positive_count:
        sentiment = "negative"
        base_confidence = 0.85 if quality == "high" else 0.70
        confidence = min(0.95, base_confidence + (negative_count * 0.03))
    else:
        sentiment = "neutral"
        confidence = 0.75 if quality == "high" else 0.65
    
    return {
        "sentiment": sentiment,
        "confidence": confidence,
        "positive_score": positive_count / max(len(text.split()), 1),
        "negative_score": negative_count / max(len(text.split()), 1)
    }


def summarize_text_handler(text: str, quality: str = "high") -> dict:
    """Summarize text with quality variations."""
    sentences = re.split(r'[.!?]+', text)
    sentences = [s.strip() for s in sentences if s.strip()]
    
    if len(sentences) <= 2:
        summary = text
    elif quality == "high":
        # Better summary: first sentence + key sentences + last sentence
        summary = sentences[0]
        if len(sentences) > 3:
            summary += ". " + sentences[len(sentences) // 2]
        if len(sentences) > 1:
            summary += ". " + sentences[-1] + "."
    else:
        # Basic summary: first and last sentences
        summary = sentences[0]
        if len(sentences) > 1:
            summary += ". " + sentences[-1] + "."
    
    return {
        "summary": summary,
        "original_length": len(text),
        "summary_length": len(summary),
        "compression_ratio": round(len(summary) / len(text) * 100, 1) if text else 0
    }


def extract_contact_info_handler(text: str, quality: str = "high") -> dict:
    """Extract contact information with quality variations."""
    data = {}
    
    # Email
    email_pattern = r'[\w\.-]+@[\w\.-]+\.\w+'
    emails = re.findall(email_pattern, text)
    if emails:
        data["email"] = emails[0] if quality == "high" else emails[-1]
    
    # Phone
    phone_patterns = [
        r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}',
        r'\+\d{1,3}[-.\s]?\d{3,4}[-.\s]?\d{3,4}[-.\s]?\d{3,4}'
    ]
    for pattern in phone_patterns:
        phones = re.findall(pattern, text)
        if phones:
            data["phone"] = phones[0]
            break
    
    # Name
    name_pattern = r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)'
    names = re.findall(name_pattern, text)
    if names:
        data["name"] = names[0] if quality == "high" else names[-1]
    
    # Address
    address_pattern = r'\d+\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*(?:,\s*[A-Z][a-z]+)+'
    addresses = re.findall(address_pattern, text)
    if addresses:
        data["address"] = addresses[0]
    
    return data


def parse_invoice_handler(text: str, quality: str = "high") -> dict:
    """Parse invoice with quality variations."""
    data = {}
    
    # Invoice number
    invoice_pattern = r'(?:Invoice|#|Invoice\s*#)\s*(\d+)'
    invoice_match = re.search(invoice_pattern, text, re.IGNORECASE)
    if invoice_match:
        data["invoice_number"] = invoice_match.group(1)
    
    # Date
    date_patterns = [
        r'(?:Date:?\s*)?([A-Z][a-z]+\s+\d{1,2},?\s+\d{4})',
        r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})'
    ]
    for pattern in date_patterns:
        date_match = re.search(pattern, text, re.IGNORECASE)
        if date_match:
            data["date"] = date_match.group(1)
            break
    
    # Bill To
    billto_pattern = r'Bill\s+To:?\s*(.+?)(?:\n|$)'
    billto_match = re.search(billto_pattern, text, re.IGNORECASE | re.MULTILINE)
    if billto_match:
        data["bill_to"] = billto_match.group(1).strip()
    
    # Items
    items = []
    item_pattern = r'(.+?)\s*:\s*\$?(\d+\.?\d*)'
    for match in re.finditer(item_pattern, text):
        desc = match.group(1).strip()
        amount = float(match.group(2))
        if desc.lower() not in ['total', 'subtotal', 'tax']:
            items.append({"description": desc, "amount": amount})
    
    if items:
        data["items"] = items
    
    # Total
    total_pattern = r'Total:?\s*\$?(\d+\.?\d*)'
    total_match = re.search(total_pattern, text, re.IGNORECASE)
    if total_match:
        data["total"] = float(total_match.group(1))
    
    return data


def extract_keywords_handler(text: str, quality: str = "high") -> dict:
    """Extract keywords with quality variations."""
    stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 'this', 'that', 'these', 'those'}
    
    words = re.findall(r'\b[A-Za-z]{3,}\b', text)
    word_freq = {}
    
    for word in words:
        word_lower = word.lower()
        if word_lower not in stop_words:
            # Capitalized words get higher weight
            weight = 2 if word[0].isupper() else 1
            word_freq[word_lower] = word_freq.get(word_lower, 0) + weight
    
    max_keywords = 15 if quality == "high" else 10
    keywords = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:max_keywords]
    
    return {
        "keywords": [k[0] for k in keywords],
        "keyword_scores": {k[0]: k[1] for k in keywords}
    }


def classify_text_handler(text: str, quality: str = "high") -> dict:
    """Classify text with quality variations."""
    categories = {
        "technology": ["technology", "software", "computer", "digital", "AI", "machine learning", "algorithm", "programming", "code"],
        "finance": ["stock", "market", "investment", "financial", "economy", "money", "business", "trading", "currency"],
        "healthcare": ["health", "medical", "patient", "hospital", "treatment", "disease", "medicine", "doctor"],
        "education": ["education", "school", "student", "learn", "study", "university", "teacher", "course"],
        "sports": ["sport", "game", "player", "team", "match", "championship", "tournament"],
        "news": ["news", "report", "announcement", "update", "breaking", "journalism"]
    }
    
    text_lower = text.lower()
    category_scores = {}
    
    for category, keywords in categories.items():
        score = sum(1 for keyword in keywords if keyword in text_lower)
        if score > 0:
            category_scores[category] = score / len(keywords)
    
    if category_scores:
        best_category = max(category_scores.items(), key=lambda x: x[1])
        base_confidence = 0.9 if quality == "high" else 0.7
        confidence = min(0.95, base_confidence + best_category[1] * 0.1)
        return {
            "category": best_category[0],
            "confidence": confidence,
            "all_scores": category_scores
        }
    else:
        return {
            "category": "general",
            "confidence": 0.5,
            "all_scores": {}
        }

