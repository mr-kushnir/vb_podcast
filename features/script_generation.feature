Feature: Podcast Script Generation with LLM
  As a system
  I want to generate an engaging podcast script using LLM
  So that I create quality audio content for listeners

  Background:
    Given I have collected 5-7 AI news articles
    And the LLM service (YaGPT) is configured
    And the date is "2026-01-14"

  Scenario: Generate podcast script from news articles
    Given I have 6 news articles
    When I request script generation
    Then the LLM should receive a prompt with all 6 articles
    And the generated script should have an introduction
    And the script should mention "Доброе утро" in the intro
    And the script should cover 5-7 main news items
    And the script should have a conclusion with insights
    And the script should include light humor and ironic comments
    And the script tone should be friendly tech-enthusiast

  Scenario: Control script reading duration
    Given I have 5 news articles
    When I request script generation with target duration 3-5 minutes
    Then the script should be between 450 and 750 words
    And the script should be optimized for speech (not dense prose)

  Scenario: Handle LLM API unavailability
    Given the LLM API is unavailable
    When I request script generation
    Then the system should retry 3 times with exponential backoff
    And if all retries fail, use a template-based script
    And log an error about LLM unavailability
    And send an alert notification

  Scenario: Handle inappropriate LLM output
    Given the LLM generates script with offensive content
    When I validate the script output
    Then the system should detect inappropriate content
    And reject the script
    And retry generation with a stricter prompt
    And log the incident for review

  Scenario: Generate script with insufficient articles
    Given I have only 2 news articles
    When I request script generation
    Then the script should still be generated
    But it should acknowledge the slow news day
    And provide deeper analysis of the available articles
    And the script should be shorter (2-3 minutes reading time)

  Scenario: Save generated script with metadata
    Given I have successfully generated a script
    When the script is validated and approved
    Then the script should be saved to "data/scripts/2026-01-14.txt"
    And metadata should be saved including:
      | field           | value                    |
      | date            | 2026-01-14              |
      | word_count      | 600                     |
      | estimated_duration | 4 minutes            |
      | article_count   | 6                       |
      | llm_model       | yagpt-4                 |
      | generation_time | timestamp               |

  Scenario Outline: Handle different article counts
    Given I have <article_count> news articles
    When I request script generation
    Then the script should be generated successfully
    And the script should appropriately cover <article_count> articles
    And the script length should be adjusted accordingly

    Examples:
      | article_count |
      | 2             |
      | 5             |
      | 7             |
      | 10            |

  Scenario: Include humor and ironic commentary
    Given I have 5 tech news articles
    And one article is about another AI hype announcement
    When I request script generation with humor enabled
    Then the script should include light ironic comments
    And the humor should be appropriate and not offensive
    And at least 2 news items should have playful commentary

  Scenario: Handle LLM timeout
    Given the LLM request takes longer than 60 seconds
    When the timeout is reached
    Then the request should be cancelled
    And the system should retry once
    And if the retry also times out, use template script

  Scenario: Validate script structure
    Given a script has been generated
    When I validate the script structure
    Then it should start with a greeting
    And it should have 3-7 distinct news sections
    And each section should have a headline and summary
    And it should end with a conclusion
    And it should not exceed 1000 words

  Scenario: Cache successful script for fallback
    Given a script has been successfully generated
    When the script is saved
    Then it should also be cached as fallback
    And the cache timestamp should be recorded
    And the cache should be used if next generation fails
