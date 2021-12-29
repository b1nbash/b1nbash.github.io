# Disclosure of vulnerability in Posten’s tracking system

<mark>Posten is not aware that anyone has been abused as a result of this vulnerability</mark>
&nbsp;  


### What is Posten Norge AS  
Posten Norge AS is a Nordic postal service company that consists of the two brands Posten and Bring. 
Posten concentrates on the private market in Norway, while Bring focuses on the corporate market in the Nordic region and private customers outside Norway  
<https://www.postennorge.no/en/about-us/our-two-brands-posten-and-bring>

### Tracking of shipments   
A tracking number can consist of up to 18 alphanumeric characters and the customers are using this tracking number to track the shipment from the sender all the way to the recipient.
When a shipment is ready for pickup, a pickup code is visible for anyone in possession of the tracking number. 

### Pickup    
Posten Norge AS has in recent years shut down almost every post office in the country due to logistic and economic reasons. Pickup location for arrived shipments is now most often in a grocery store. This means that the shipments are handled by the employees working in the grocery store, not employees from Posten.  
When a customer picks up a shipment ordered online from the pickup location, the customer is required to say either a pickup-code, shipment number, parcel number or a barcode
in combination with their name/show ID


![Screenshot](images/trackingHome.jpg?raw=true)


The figure above show a customer tracking their shipment, and according to the result, the shipment  is ready for pickup. 

&nbsp;
## Possible vulnerability    
I got a tip that the tracking numbers Posten uses are not randomly generated, i.e., the tracking numbers increase as new customers receive or send shipments. Thus, it could be possible to write a script to somehow fetch all shipments ready for pickup and save these tracking numbers including their pickup codes into a database.
This data could then be used to pick up shipments, gambling that the clerk wouldn’t ask for our name, only the pickup code.

&nbsp;
### Initial investigating    
My first plan was to collect some data to explore this possibility. I reckoned a simple python script using the requests library would do the job. Viewing the source code of the tracking page (<https://sporing.posten.no/sporing/?lang=en>), I saw that the page was using JavaScript and this meant I couldn’t use this URL to get the data I wanted, at least not easily. I started to research how to somehow web-scrape JavaScript-pages, but I felt that all the solutions were old and outdated.  

After some time, I googled “Posten API” to see if there was an API available. Apparently Bring, Posten’s corporate service, offered multiple API’s (<https://developer.bring.com/>) but none of these was what I was looking for. So, if Bring had API’s, why wouldn’t Posten have it too?  
With this in mind, I further investigated the tracking page by opening developer tools, and when looking for the type “fetch”, I finally found a tracking API link (<https://sporing.bring.no/tracking/api/fetch/>).  
Now the fetching of data could begin. 

&nbsp;
### Collecting data   
I had recently bought some clothes from the clothing/fashion shop “H&M” and decided to use the tracking number for this shipment as an initial start for iteration in the script. A range of 300 seemed enough to start with. I expected my own shipment data to display first since the loop started on my tracking number.


![Screenshot](images/firstScript.jpg?raw=true)

&nbsp;  

Already after a few iterations I had got a lot of data to inspect.  


![Screenshot](images/initialResult.JPG?raw=true)

&nbsp;  

And as expected I found my own shipment data:  


![Screenshot](images/jsonPrettyEx1.JPG?raw=true)

&nbsp;  

Okay, I could now filter my output to only show me data where “dateOfEstimatedDelivery” was one week ahead for example. And maybe filter on status, i.e. only print data when “status” = ready for pickup/in transit. And, hopefully I would get some pickup codes as well.  

&nbsp;

### The vulnerability  
When I continued inspecting the output from my script, I noticed something. Suddenly names were appearing in the JSON output. I thought it was a bit strange for Posten to include the name of the receiver in the tracking number, but further inspection showed that the name was not the receiver, it was the sender. Wasn’t H&M the sender of these shipments?  

I was confused and wanted to get a more graphical understanding. I pasted the tracking number from the script into Posten’s website as if I were to track my own shipment, and this appeared:

![Screenshot](images/returnWithNameHidden.jpg?raw=true)

&nbsp;  

“Shipment from **** ****”  
“Sender **** ****”  
I quickly realized that this was a return shipment to H&M. Notice the H&M logo and the product name in the bottom right corner (“Service Parcel Return Service”). This would mean that this **** had bought something from H&M, but later returned it.
It kind of made sense, because I guess H&M needs to know if a customer returns something and when the return arrives, H&M can complete the refund.  

  

&nbsp;  

But then I saw my own name in the output. Why would my name show up in a return shipment tracking number? I hadn’t returned anything ...

![Screenshot](images/trackingReturn.jpg?raw=true)


Notice that the return tracking number (on the right) is created before I received the shipment (on the left). 

&nbsp;  

My reasoning to this was that when a customer orders something from H&M, H&M immediately creates a return tracking number. This makes it easier for the customer to return one or more items. (A return sticker is included in each shipment).  

Ok, so in essence I got a load of tracking numbers and a load of return tracking numbers, names included.  
Was there a pattern I could exploit? Yes, indeed!  

After further investigating the data, I concluded that the return tracking number was always 1-20 greater than the customer’s tracking number.
I decided to create a simple database that showed tracking number, status, pickup code, arrival city and the possible buyer  

[Script source code](https://github.com/b1nbash/b1nbash.github.io/tree/main/script/fetchTrackingNo.py)
&nbsp;  


![Screenshot](images/possibleBuyersHidden.jpg?raw=true)  

How could I be sure that the names in the column “possibleBuyer” were in fact the buyer, and hence there existed a vulnerability in the system? I couldn’t, therefore the prefix “possible”. But I had a way to strengthen my suspicions.  
Norway is a large country in relative to the population, and we have a lot of small villages. So, if I live in a small village with a population of 1000 or less, and have a unique name, there is a very high probability that I am the only one with that name in that particular village.  
Therefore, my assumption was if I could match a “possibleBuyer/city” with the result from <http://www.1881.no> (Database of names, numbers and addresses based upon the National Population Register), I could with great certainty say that “possibleBuyer” in fact was the actual buyer. Especially if that matching city was a small village with a small population.  

So, I started experimenting. In the image above, nr. 1982 shows the village “Ådalsbruk” and the possible buyer living in this village has a rather unique name. This village has a population of 595 (2008). This was perfect as the probability of a person named exactly the same in a village with that population size is very low. I looked up the name in 1881.no, and there was only one person with that exact name in the entire country. And yes, this person was registered in Ådalsbruk.  
Okay, my assumption seemed correct . However, this approach was not always 100% successful because people don’t have to update their address in the National Register when they move to another place. A person can be registered in Bergen, but still live in Oslo, or even Paris, and get mail to the address in Oslo or Paris.  

After some more testing, I felt now pretty confident about the relationship between the tracking number and the return tracking number. In theory I could pick up any shipment from H&M anywhere in the country, provided that the clerk at the pickup location didn’t ask for my ID.  

&nbsp;  

When I had enough data to back up my theory, I informed Posten Norge AS about my findings. The day after, I received an email that this bug was now fixed.  


&nbsp;
&nbsp;
## PS  

While working with this report I noticed something else, something that I didn’t observe in the start of the research.
In my period of testing, I had gotten hold of some old tracking numbers, much older than my own tracking number. How I found these I don’t remember. 
Anyways, when investigating the JSON of these I found not only names but addresses too.  


![Screenshot](images/nameAndAddress.jpg?raw=true)

I immediately notified Posten Norge AS about this as well, and they responded with deleting the tracking numbers all together. The reason for this to happen was apparently a minor deviation between the production and backup system, involving just a few old tracking numbers.  

&nbsp;
&nbsp;
## PSS  

Posten Norge AS deserves credit for taking this matter seriously and I am impressed of how quick they fixed the issues.

