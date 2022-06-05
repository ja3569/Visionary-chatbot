
const request = require("request");
const cheerio = require("cheerio");
const axios = require('axios');

//const url = 'https://www.eventbrite.com/d/united-states--new-york/music--events/?page=1';
const url = "https://www.eventbrite.com/d";
const location = "/united-states--new-york/"
const topics = ['business', 'food-and-drink', 'music', 'health', 'charity-and-causes', 'film-and-media', 'travel-and-outdoor', 'science-and-tech']
const suffix = "--events/?page=1"
const link = 'https://www.eventbrite.com/d/united-states--new-york/music--events/?page=1';


function url_generator(topic_id) {
    var link = url + location + topics[topic_id] + suffix
    return link;
}

function scraper(link, topic_name) {
    
    axios(link)
    .then(response  => {
        const html = response.data
        const event_storage = cheerio.load(html)
        const event_list = []
        const title_list = []
        //console.log(event_storage(".music_events--bucket-wrapper", html))
        event_storage('.eds-event-card-content__content__principal', html).each(function(){
            const topic = topic_name;
            const title = event_storage(this).find(".eds-is-hidden-accessible").text()
            const time = event_storage(this).find('.eds-event-card-content__sub-title').text()
            const location_text = event_storage(this).find('.card-text--truncated__one').text()
            const location = String(location_text.indexOf(" •"))>0 ? String(location_text).substr(0, String(location_text).indexOf(" •")) : String(location_text)
            const address =  String(location_text).replace(" • ", ", ")
            const event = {
                topic,
                title,
                time,
                location,
                address
            }
            if (!title_list.includes(title)) {
                event_list.push(event)
            }
            title_list.push(title);
            
        })
        console.log(event_list);
    })
    .catch(error => console.log(error))
    
}

function json_generator() {
    for (let i = 0; i < topics.length; i++) {
        const link = url_generator(i);
        scraper(link, topics[i]);
    }
}

//scraper(link, "business");
json_generator();

