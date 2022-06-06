//Scrape by API
const request = require("request");
const cheerio = require("cheerio");
const axios = require('axios');



const url = 'https://data.cityofnewyork.us/resource/i4kb-6ab6.json';

let load_api = async () => {
    await axios.get(url)
    .then(response => {
        json_file = response.data
        const info = []
        let str_list = ''
        for (let i = 0; i < json_file.length-6; i++) {
            cur_info = response.data[i]
            const name = cur_info["organization_name"].replace("'", "");
            const id = i
            const website = cur_info["website"]["url"].replace("'", "");
            const description = cur_info["volunteer_program_description"].replace("'", "");
            const location = cur_info["street_address"].replace("'", "");
            const postcode = cur_info["postcode"]
            info.push({
                name,
                //id,
                //website,
                //description,
                //location,
                //postcode
            })
            let cur_text = "{'name': '" + name + "', 'id': '" + id + "', 'website': '" + website + "', 'description': '" + description + "', 'location': '" + location + "', 'postcode': '" + postcode + "'}"
            str_list = str_list.concat(', \n' + cur_text)
            
        }
        console.log(str_list);
        
        return response
        
    })
    .catch(error => console.log(error))
};

load_api()
