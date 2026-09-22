# Bugfix Requirements Document

## Introduction

The debate purchase feature has several critical issues affecting user experience and functionality. Product links are broken (leading to DuckDuckGo bad request pages instead of actual product pages), product images are not displaying (showing yellow placeholders), product information is not prominently displayed in cards, and the recommendation text is too subtle. These issues prevent users from effectively comparing and purchasing products through the debate interface.

## Bug Analysis

### Current Behavior (Defect)

1.1 WHEN a user clicks on any product link in the debate purchase interface THEN the system navigates to a DuckDuckGo bad request page instead of the actual product page on the e-commerce site

1.2 WHEN product offers are displayed in the offers list or chosen card THEN the system shows a yellow line/placeholder instead of actual product images

1.3 WHEN the chosen offer card is displayed THEN the system does not prominently show the product image, name, and price together in a clear visual hierarchy

1.4 WHEN offer cards are displayed in the provider-grouped lists THEN the system does not prominently display product images alongside the title and price

1.5 WHEN the recommended site is shown THEN the system displays the text in a small, non-emphasized format that is difficult for users to notice

### Expected Behavior (Correct)

2.1 WHEN a user clicks on any product link in the debate purchase interface THEN the system SHALL navigate directly to the exact product page on the exact e-commerce site (Amazon, Flipkart, Blinkit, or web source)

2.2 WHEN product offers are displayed in the offers list or chosen card THEN the system SHALL display actual product images fetched either through scraping or a free public API

2.3 WHEN the chosen offer card is displayed THEN the system SHALL prominently display the product image, item name (title), and item price in a clear visual hierarchy with appropriate sizing and emphasis

2.4 WHEN offer cards are displayed in the provider-grouped lists THEN the system SHALL prominently display product images (not placeholders) alongside the title and price for all items

2.5 WHEN the recommended site is shown THEN the system SHALL display the recommendation text in medium-sized, emphasized formatting so users can clearly identify which site is recommended

### Unchanged Behavior (Regression Prevention)

3.1 WHEN the debate logic scores and selects the best offer THEN the system SHALL CONTINUE TO use the existing scoring algorithm based on price, trust, and delivery ETA

3.2 WHEN multiple offers are aggregated from different providers THEN the system SHALL CONTINUE TO group offers by provider (Amazon, Flipkart, Blinkit, Web) in the UI

3.3 WHEN the AI debate generates role-based recommendations THEN the system SHALL CONTINUE TO display the four debate roles (FrugalCoach, ValueAnalyst, ConvenienceAdvocate, Referee) with their respective styling

3.4 WHEN savings calculations are performed THEN the system SHALL CONTINUE TO calculate and display savings compared to other offers

3.5 WHEN the user searches for a product with a specific priority (cheapest, fastest, best_overall) THEN the system SHALL CONTINUE TO respect that priority in the offer scoring and selection
