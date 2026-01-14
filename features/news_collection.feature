Feature: News Collection from TechCrunch AI
  As a system
  I want to automatically parse AI news from TechCrunch
  So that I have up-to-date content for the podcast

  Background:
    Given the TechCrunch AI category URL is "https://techcrunch.com/category/artificial-intelligence/"
    And the system time is "2026-01-14 10:00:00 UTC"

  Scenario: Successfully parse recent AI news articles
    Given TechCrunch is available
    And there are 10 AI articles published in the last 24 hours
    When I trigger the news collection process
    Then I should receive 10 articles
    And each article should have a title
    And each article should have a description
    And each article should have a URL
    And each article should have a publication date
    And all articles should be published within the last 24 hours

  Scenario: Filter articles by 24-hour window
    Given TechCrunch is available
    And there are 5 articles from the last 12 hours
    And there are 3 articles from 30 hours ago
    When I trigger the news collection process
    Then I should receive 5 articles
    And all returned articles should be from the last 24 hours

  Scenario: Handle insufficient articles gracefully
    Given TechCrunch is available
    And there are only 2 articles in the last 24 hours
    When I trigger the news collection process
    Then I should receive 2 articles
    And a warning should be logged about insufficient content
    And the system should proceed with available articles

  Scenario: Save parsed articles in structured format
    Given TechCrunch is available
    And there are 5 articles available
    When I trigger the news collection process
    And the articles are successfully parsed
    Then articles should be saved to "data/news/2026-01-14.json"
    And the JSON should be valid
    And the JSON should contain an array of article objects
    And each article should have keys: title, description, url, date

  Scenario Outline: Handle network errors with retry logic
    Given TechCrunch returns <error_type>
    When I trigger the news collection process
    Then the system should retry <retry_count> times
    And if all retries fail, an error should be logged
    And the process should use cached articles if available

    Examples:
      | error_type      | retry_count |
      | connection_timeout | 3        |
      | 503_service_unavailable | 3   |
      | dns_resolution_error | 2      |

  Scenario: Handle HTML structure changes
    Given TechCrunch HTML structure has changed
    And the article selector is not found
    When I trigger the news collection process
    Then the system should log a parsing error
    And the system should send an alert notification
    And the system should use cached articles from the previous day

  Scenario: Handle rate limiting from TechCrunch
    Given TechCrunch returns HTTP 429 Too Many Requests
    When I trigger the news collection process
    Then the system should wait for the retry-after period
    And then retry the request
    And if rate limit persists, use cached articles

  Scenario: Remove duplicate articles
    Given TechCrunch is available
    And there are 7 unique articles
    And 2 of them are duplicates by URL
    When I trigger the news collection process
    Then I should receive 7 unique articles
    And duplicates should be filtered out

  Scenario: Handle articles with missing fields
    Given TechCrunch is available
    And article 1 has no description
    And article 2 has no publication date
    And article 3 has all required fields
    When I trigger the news collection process
    Then article 1 should use an empty description
    And article 2 should use the current date as fallback
    And article 3 should be included normally
    And all articles should be valid

  Scenario: Cache successful results
    Given TechCrunch is available
    And there are 5 articles available
    When I trigger the news collection process successfully
    Then the articles should be cached
    And the cache should have a timestamp
    And the cache should be stored in "cache/latest_news.json"
