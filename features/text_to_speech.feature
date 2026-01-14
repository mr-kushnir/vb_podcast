Feature: Text-to-Speech Audio Generation
  As a system
  I want to convert podcast script to audio using ElevenLabs
  So that I produce high-quality audio content for listeners

  Background:
    Given I have a generated podcast script
    And the script is 600 words long
    And ElevenLabs API is configured with API key
    And I have sufficient API quota remaining

  Scenario: Generate audio from script using ElevenLabs
    Given the podcast script is ready
    When I request TTS generation
    Then the system should call ElevenLabs API
    And use a friendly, energetic voice
    And generate an MP3 file
    And the audio duration should be 3-5 minutes
    And the audio quality should be at least 128kbps

  Scenario: Select appropriate voice settings
    Given I need to generate audio
    When I configure the voice settings
    Then I should use a voice that is:
      | characteristic  | value              |
      | energy_level    | high               |
      | friendliness    | very_friendly      |
      | age             | young_adult        |
      | language        | russian            |
      | stability       | 0.7                |
      | similarity      | 0.8                |

  Scenario: Handle ElevenLabs API unavailability
    Given ElevenLabs API returns 503 Service Unavailable
    When I request TTS generation
    Then the system should retry 3 times with backoff
    And if all retries fail, log the error
    And store the script for later retry
    And send alert notification about TTS failure

  Scenario: Handle API quota exceeded
    Given ElevenLabs API returns 429 Quota Exceeded
    When I request TTS generation
    Then the system should check the quota reset time
    And log a warning about quota limits
    And schedule retry after quota reset
    And send notification about quota issue

  Scenario: Save audio file with metadata
    Given audio has been successfully generated
    When the audio file is received
    Then it should be saved to "data/audio/2026-01-14.mp3"
    And metadata should be saved:
      | field           | value                    |
      | date            | 2026-01-14              |
      | duration        | 4:23                    |
      | file_size       | 4.2 MB                  |
      | voice_id        | energetic_russian_male  |
      | bitrate         | 128kbps                 |
      | generated_at    | timestamp               |

  Scenario: Upload audio to Yandex Object Storage
    Given audio file has been generated locally
    When I upload to cloud storage
    Then the file should be uploaded to S3 bucket
    And the S3 key should be "podcasts/2026-01-14.mp3"
    And the file should have public-read permissions
    And I should receive a public URL
    And the URL should be stored in the database

  Scenario: Handle upload failure to storage
    Given audio file has been generated
    And S3 upload fails with network error
    When I attempt to upload
    Then the system should retry upload 3 times
    And if all retries fail, keep local file
    And log the upload failure
    And schedule background retry job

  Scenario: Validate audio quality
    Given audio has been generated
    When I validate the audio file
    Then the file should be a valid MP3
    And the duration should match expected range (±30 seconds)
    And the file size should be reasonable (2-10 MB)
    And the audio should not have silence longer than 3 seconds

  Scenario: Handle Russian text with English tech terms
    Given the script contains Russian text
    And it includes English terms like "LLM", "API", "GPT"
    When I request TTS generation
    Then the pronunciation should handle mixed language correctly
    And tech terms should be pronounced naturally
    And the overall audio should sound fluent

  Scenario Outline: Handle different script lengths
    Given the script has <word_count> words
    When I request TTS generation
    Then the audio duration should be approximately <duration> minutes
    And the generation should complete successfully

    Examples:
      | word_count | duration |
      | 300        | 2        |
      | 600        | 4        |
      | 900        | 6        |

  Scenario: Handle poor audio quality detection
    Given audio has been generated
    When quality check detects distortion or artifacts
    Then the system should log a quality warning
    And attempt regeneration with different settings
    And if quality remains poor, accept but flag for review

  Scenario: Cache audio generation results
    Given audio has been successfully generated and uploaded
    When the process completes
    Then the audio URL should be cached
    And metadata should be cached for quick access
    And the cache entry should include generation timestamp
