Feature: Automated Daily Podcast Generation
  As a system
  I want to run the podcast pipeline on schedule
  So that new episodes are published every morning automatically

  Background:
    Given the cron job is configured for 7:00 AM UTC
    And all necessary API keys are configured
    And the previous episode was generated successfully

  Scenario: Successful daily pipeline execution
    Given it is 7:00 AM UTC on 2026-01-14
    When the cron job triggers
    Then the news collection should execute
    And the script generation should execute
    And the TTS generation should execute
    And the audio should be uploaded to storage
    And the episode should be added to the database
    And the RSS feed should be updated
    And a success log entry should be created

  Scenario: Log all pipeline stages
    Given the pipeline is running
    When each stage completes
    Then a log entry should be written to "logs/pipeline-2026-01-14.log"
    And each log entry should include:
      | field           |
      | timestamp       |
      | stage           |
      | status          |
      | duration        |
      | details         |
    And the log level should be INFO for success

  Scenario: Handle news collection failure
    Given the cron job triggers at 7:00 AM
    And the news collection fails after all retries
    When the pipeline reaches the failure point
    Then an ERROR should be logged
    And the pipeline should attempt to use cached news
    And if cache exists, continue with cached data
    And if no cache, skip to next day
    And send alert notification about the failure

  Scenario: Handle script generation failure
    Given news collection succeeded
    But LLM script generation fails
    When the pipeline handles the failure
    Then it should retry script generation 2 times
    And if all fail, use a template-based script
    And log a WARNING about fallback script
    And send notification about LLM issue
    And continue to TTS stage

  Scenario: Handle TTS generation failure
    Given news and script stages succeeded
    But TTS generation fails
    When the pipeline handles the failure
    Then it should log the TTS error
    And save the script for manual review
    And schedule a retry job for 1 hour later
    And send immediate alert notification
    And mark the episode as "pending audio"

  Scenario: Handle partial pipeline success
    Given news collection succeeded
    And script generation succeeded
    But TTS and upload failed
    When the pipeline completes
    Then the episode should be marked as "incomplete"
    And the script should be saved
    And a retry job should be scheduled
    And the portal should show the transcript only
    And an alert should notify the admin

  Scenario: Send success notification
    Given the pipeline completed successfully
    When all stages are done
    Then a success notification should be sent
    And the notification should include:
      | field                |
      | episode_date         |
      | total_duration       |
      | article_count        |
      | audio_url            |
      | pipeline_duration    |
    And the notification method should be Telegram (optional)

  Scenario: Send failure notification with details
    Given the pipeline failed at script generation stage
    When the failure is detected
    Then an error notification should be sent immediately
    And the notification should include:
      | field                |
      | failed_stage         |
      | error_message        |
      | timestamp            |
      | retry_status         |
      | cache_availability   |

  Scenario: Prevent duplicate executions
    Given the cron job triggered at 7:00 AM
    And the pipeline is currently running
    When the cron triggers again due to a bug
    Then the second execution should be prevented
    And a lock file should exist at "locks/pipeline.lock"
    And the duplicate attempt should be logged
    And the original execution should continue

  Scenario: Handle long-running pipeline
    Given the pipeline started at 7:00 AM
    And it is still running at 7:30 AM
    When the timeout threshold is reached
    Then a warning should be logged
    And if it exceeds 1 hour, force termination
    And send an alert about the timeout
    And clean up any partial results

  Scenario: Cleanup old episodes
    Given there are 60 episodes in the database
    And the cleanup policy is to keep 30 days
    When the cleanup task runs
    Then episodes older than 30 days should be archived
    And their audio files should be moved to cold storage
    And they should still be accessible in archive
    And database records should be marked as archived

  Scenario: Monitor storage quota
    Given the Yandex S3 bucket is monitored
    When storage usage exceeds 80%
    Then a warning notification should be sent
    And old episodes should be compressed
    And if usage exceeds 95%, stop new uploads
    And send critical alert to admin

  Scenario: Recover from previous day's failure
    Given yesterday's pipeline failed completely
    And today's pipeline is about to run
    When today's cron triggers
    Then it should check for yesterday's failure
    And attempt to generate yesterday's missing episode first
    And then proceed with today's episode
    And both episodes should be published

  Scenario: Health check endpoint
    Given the system is deployed
    When I call the /health endpoint
    Then it should return status 200 OK
    And the response should include:
      | field                    |
      | status                   |
      | last_successful_run      |
      | next_scheduled_run       |
      | storage_available        |
      | api_quotas_remaining     |

  Scenario: Scheduled maintenance mode
    Given a maintenance window is scheduled
    When the cron job tries to run during maintenance
    Then the pipeline should be skipped
    And a log entry should explain the skip
    And no error notifications should be sent
    And the next run should proceed normally

  Scenario: Graceful shutdown
    Given the pipeline is running
    When a shutdown signal is received (SIGTERM)
    Then the current stage should complete if possible
    And partial progress should be saved
    And resources should be cleaned up
    And a log entry should record the shutdown
    And the lock file should be removed

  Scenario Outline: Handle different cron schedules
    Given the cron is set to <schedule>
    When the time matches the schedule
    Then the pipeline should execute
    And all stages should complete successfully

    Examples:
      | schedule                  |
      | 0 7 * * * (7 AM daily)   |
      | 0 */6 * * * (every 6 hrs)|
      | 0 8 * * 1-5 (weekdays)   |

  Scenario: Database transaction safety
    Given the pipeline is updating the database
    When a failure occurs mid-transaction
    Then the transaction should rollback
    And the database should remain consistent
    And no partial records should exist
    And the next run should start with clean state
