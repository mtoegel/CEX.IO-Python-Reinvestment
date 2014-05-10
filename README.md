﻿CEX.IO-Python-Reinvestment
==========================
\n
Little project I decided to work on for the Raspberry Pi\n
\n
Got slightly introduced to Python in a class, like a 1 day intro, so I decided\n
to try to work on a reinvestment program for my Raspberry Pi to get into Python a bit.\n
\n
The Cex.io API was slightly modified to work for Python 3.3.2 since the one from their git threw errors for me.\n
The start.py script is the main program. It uses colorama for text coloring in the command line.\n
\n
*I'm working on a second version of this project, but I still have the old one included.\n
\n
Instructions for the old version (start_old_method.py):\n
1. On the first run it will ask you to setup a config file in which you can add multiple Cex.io accounts.\n
2. You'll need a display name for the command line output, the username for the account (api), the api key, and api secret.\n
3. Then it'll ask you to choose an reinvestment method, basic selections so far:\n
    * "average" - It will only purchase GHS if the last trade is lower than the "today's" average.\n
    * "percent" - It will only purchase GHS if the last trade is within x% of the lowest trade for "today".\n
    * "any" - It will purchase GHS at the last trade value.\n
3. Then it will ask you to input a delay between interations or cycles of accounts. The default is 180 minutes and minumum is 1 minute.\n
It also attempts to limit the API calls to keep it below the threshold of 600/10 minutes so your IP doesn't get banned.\n
\n
Once the config file is set, it'll save it to a text file which you can manually edit later, or delete/rename it if you want to rebuilt it.\n
Then the script will run until the process is killed.\n
If you want to run it via a cron you can remove the "while True:" line and remove the indentations from the code that follows.\n
\n
* If the account has < 5 GHS it buys what it can according to the rules provided.\n
* If the account has >= 5 GHS it'll try to purchase a whole number GHS, the minimum being 1 GHS.\n
* It also tries to make sure that a transaction won't leave you with less than .00011 BTC.\n
* It has a built in 30 second delay between switching accounts.\n
* Currently this version invests for the Future Hashrate for May or FMH/BTC until May 26th when it's over. I'll update this around that time to remove the unnecessary code or update it to another future buy possibly. After that day the currency set will be 'GHS/BTC'. If you don't want this you can remove the if statement checking the date and the currency change under the reinvest function. In the future I plan to give an option.\n
\n
Instructions for new version (start.py):\n
1. On the first run it'll ask you to setup a config file (the format is different from the old version).\n
2. It'll ask you to add accounts by providing a display name (for the console), cexio username, api key, and api secret.\n
3. Next it'll ask you which currency you'd like to reinvest into. Default is GHS and has only been tested with GHS and the temp currency of FHM) Though other possible options should be LTC, NMC, or BTC.\n
4. Then it'll go through a list of other currencies and ask if you'd like to try to invest them into the chosen currency above.\n
5. For each selected currency it'll ask you for a reinvestment method:\n
	* "average" - It will only purchase GHS if the last trade is lower than the "today's" average.\n
    * "percent" - It will only purchase GHS if the last trade is within x% of the lowest trade for "today".\n
    * "any" - It will purchase GHS at the last trade value.\n
6.Finally, it will ask you to input a delay between interations or cycles of accounts. The default is 180 minutes and minumum is 1 minute.\n
* The limits and basic functionality from the old version are still relevant so it's worth reading through the old instructions.\n
* However, the FHM/BTC is just an option of labeling the currency in step 3 to FHM, but it doesn't do the date checking yet like it does in the old version.\n
\n
**To-DO:**\n
* []Optimize and cleanup the structure and code\n
* []Add other error checks, prevent errors from breaking code loop\n
* []Test it on Raspberry Pi\n
* []Add email feature?\n
* []Make sure there aren't any resource leaks\n
* [x]Other reinvestment methods (added in new version)\n
* [x]Provide currency choice (added in new version)\n
* [x]Add reinvestment for LTC and NMC either to BTC or GHS if applicable with separate strategies (added in new version)\n
* []Implement better handling of the temporary currencies (i.e., FHM or FHJ if they continue this)\n
\n
Since I'm using this project too, I'll update this repo as I make changes to my version.\n
This project is provided AS-IS.\n
\n
If you'd like to support this project you may send BTC to 17jVTWiYSUMjBKN2FYkzjtGHohgLKQi4xs.