# Python Discord Bot

## Features
- Polls
- Manage reminders
- Summarize text using Gemini
- Music player
- Run moderation commands (kick, ban, mute)
- Filter words
- Integrated joke and weather API
- Made a report ticket system 

## Planned Improvements
I wanted to make the current version better, like make the music player uses commands like `!join` to join VC then you can `!play` songs by sending it YouTube video links, `!queue` to add songs to queue etc, instead I wanted to do an embed with buttons instead of commands like `!skip` or `!stop` you can just press the button for it to change or stop songs, same thing with the polls, the one I implemented uses reactions as polls and not embed buttons so I would like to change that too. Now I just made a summarize feature for Gemini, I wanted to test out more with the API and add more interesting features. I'm fine with the reminder system as I used `parsetime` which just converts reminder texts conveniently like if I took `remindme tomorrow` it'll just set reminder for tomorrow, if I had to add more, I'll add like a every 5 minutes send a ping if I don't respond to the reminder with a message so I don't miss my reminder. For the polls i would add a `!endpoll` which would geenrate a message saying final results of poll.

If I was given more time I would implement all these features.
