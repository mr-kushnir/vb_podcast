Feature: Web Portal for Podcast Listening
  As a user
  I want to listen to podcasts on a web portal
  So that I stay informed about AI news every morning

  Background:
    Given the web portal is deployed at "podcast.rapidapp.ru"
    And there are 5 podcast episodes in the archive
    And the latest episode is from "2026-01-14"

  Scenario: View homepage with latest episode
    Given I visit the homepage
    Then I should see a minimalist dark-mode design
    And I should see the audio player with the latest episode
    And the player should show episode date "2026-01-14"
    And the player should show episode duration
    And the player should have play/pause controls
    And the player should have a progress bar
    And the player should have volume controls

  Scenario: Play the latest podcast episode
    Given I am on the homepage
    When I click the play button
    Then the audio should start playing
    And the progress bar should update in real-time
    And the play button should change to pause
    And the page title should show "▶ AI Morning Podcast"

  Scenario: Navigate episode archive
    Given I am on the homepage
    When I scroll down to the archive section
    Then I should see a list of previous episodes
    And each episode should display:
      | field           |
      | date            |
      | duration        |
      | play button     |
      | download link   |
    And episodes should be sorted newest first

  Scenario: Play an archived episode
    Given I am viewing the archive
    When I click play on the episode from "2026-01-13"
    Then the main player should load that episode
    And the audio should start playing
    And the current episode indicator should update

  Scenario: Download podcast episode
    Given I am viewing an episode
    When I click the download button
    Then the MP3 file should be downloaded
    And the filename should be "ai-morning-2026-01-14.mp3"

  Scenario: Subscribe via RSS feed
    Given I am on the homepage
    When I click the RSS feed button
    Then I should be redirected to "/rss.xml"
    And the RSS feed should be valid XML
    And the feed should include all published episodes
    And each episode should have:
      | field           |
      | title           |
      | description     |
      | audio_url       |
      | pub_date        |
      | duration        |

  Scenario: Validate RSS feed format
    Given the RSS feed is generated
    When I validate the RSS XML
    Then it should conform to RSS 2.0 specification
    And it should include iTunes podcast tags
    And the enclosure URL should be publicly accessible
    And the media type should be "audio/mpeg"

  Scenario: Responsive design on mobile
    Given I visit the portal on a mobile device
    Then the layout should adapt to small screens
    And the audio player should remain functional
    And text should be readable without zooming
    And buttons should be touch-friendly (min 44px)
    And the site should load within 3 seconds

  Scenario: Dark mode by default
    Given I visit the portal
    Then the background should be dark (#1a1a1a or darker)
    And text should be light colored for contrast
    And the player controls should be visible against dark bg
    And there should be no bright flashes

  Scenario: Handle missing audio gracefully
    Given an episode exists in the database
    But the audio file is not available on S3
    When I try to play that episode
    Then an error message should be displayed
    And the message should say "Audio temporarily unavailable"
    And I should have an option to read the transcript
    And an alert should be logged for investigation

  Scenario: Display episode transcript
    Given I am viewing an episode
    When I click "Show Transcript"
    Then the full podcast script should be displayed below
    And the transcript should be readable and formatted
    And I should be able to copy the text

  Scenario: Handle no episodes available
    Given there are 0 episodes in the system
    When I visit the homepage
    Then I should see a message "First episode coming soon"
    And there should be no broken player
    And the page should still look professional

  Scenario: SEO optimization
    Given the portal is deployed
    When a search engine crawls the page
    Then the page should have proper meta tags:
      | tag              | content                          |
      | title            | AI Morning Podcast              |
      | description      | Daily AI news summary podcast   |
      | og:type          | website                         |
      | og:image         | podcast cover image URL         |
    And structured data for Podcast should be present

  Scenario: Audio player keyboard controls
    Given I am on the homepage with focus on player
    When I press the spacebar
    Then the audio should toggle play/pause
    When I press the right arrow key
    Then the audio should skip forward 10 seconds
    When I press the left arrow key
    Then the audio should skip backward 10 seconds

  Scenario: Handle concurrent users
    Given 100 users visit the portal simultaneously
    When they all try to play episodes
    Then the server should handle the load
    And audio should stream without buffering issues
    And the page should remain responsive
    And no users should see errors

  Scenario: Browser compatibility
    Given I visit the portal
    When using <browser>
    Then the audio player should work correctly
    And all functionality should be available
    And the design should render properly

    Examples:
      | browser           |
      | Chrome 120+       |
      | Firefox 120+      |
      | Safari 17+        |
      | Edge 120+         |
      | Mobile Safari iOS |
      | Chrome Android    |

  Scenario: Analytics tracking (optional)
    Given analytics is enabled
    When a user plays an episode
    Then a play event should be tracked
    And the episode ID should be recorded
    And no personal data should be collected
    And analytics should not slow down the page
