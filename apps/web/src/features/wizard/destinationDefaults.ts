export interface DayDefault {
  region: string;
  attractions: string[];
}

export const ANDAMAN_DAY_DEFAULTS: DayDefault[] = [
  { region: "Port Blair", attractions: ["Cellular Jail", "Corbyn's Cove Beach", "Marina Park and Flag Point"] },
  { region: "Port Blair", attractions: ["Ross Island (NSCB Island)", "North Bay Island", "Chidiya Tapu"] },
  { region: "Swaraj Dweep (Havelock)", attractions: ["Radhanagar Beach", "Elephant Beach", "Kalapathar Beach"] },
  { region: "Shaheed Dweep (Neil)", attractions: ["Bharatpur Beach", "Natural Bridge", "Laxmanpur Beach"] },
  { region: "Baratang", attractions: ["Limestone Caves", "Mud Volcano", "Jolly Buoy Island"] },
  { region: "Port Blair", attractions: ["Samudrika Naval Marine Museum", "Chatham Saw Mill", "Anthropological Museum"] },
];

export const RAJASTHAN_DAY_DEFAULTS: DayDefault[] = [
  { region: "Jaipur", attractions: ["Amber Fort", "City Palace", "Hawa Mahal"] },
  { region: "Jaipur", attractions: ["Jantar Mantar", "Nahargarh Fort"] },
  { region: "Jodhpur", attractions: ["Mehrangarh Fort", "Jaswant Thada"] },
  { region: "Udaipur", attractions: ["City Palace", "Lake Pichola"] },
  { region: "Jaisalmer", attractions: ["Jaisalmer Fort", "Patwon Ki Haveli", "Sam Sand Dunes"] },
  { region: "Sawai Madhopur", attractions: ["Ranthambore National Park", "Ranthambore Fort"] },
];

export const KASHMIR_DAY_DEFAULTS: DayDefault[] = [
  { region: "Srinagar", attractions: ["Dal Lake Shikara", "Mughal Gardens", "Shankaracharya Temple"] },
  { region: "Gulmarg", attractions: ["Gulmarg Gondola", "Kongdoori", "Apharwat Peak"] },
  { region: "Pahalgam", attractions: ["Betaab Valley", "Aru Valley", "Chandanwari"] },
  { region: "Sonamarg", attractions: ["Thajiwas Glacier", "Sindh River View"] },
  { region: "Doodhpathri", attractions: ["Doodhpathri Meadows", "Shaliganga River"] },
  { region: "Srinagar", attractions: ["Old City Heritage Walk", "Jamia Masjid"] },
];

export const GOA_DAY_DEFAULTS: DayDefault[] = [
  { region: "Candolim", attractions: ["Fort Aguada", "Candolim Beach", "Sinquerim Beach"] },
  { region: "Baga", attractions: ["Baga Beach Water Sports", "Calangute Beach"] },
  { region: "Vagator", attractions: ["Chapora Fort", "Vagator Beach Sunset", "Anjuna Flea Market"] },
  { region: "Panaji", attractions: ["Fontainhas Latin Quarter", "Mandovi River Cruise", "Miramar Beach"] },
  { region: "Old Goa", attractions: ["Basilica of Bom Jesus", "Se Cathedral"] },
  { region: "Palolem", attractions: ["Palolem Beach", "Butterfly Beach", "Cabo de Rama Fort"] },
];

export const KERALA_DAY_DEFAULTS: DayDefault[] = [
  { region: "Kochi", attractions: ["Fort Kochi & Chinese Fishing Nets", "Mattancherry Palace", "Marine Drive"] },
  { region: "Munnar", attractions: ["KDHP Tea Museum & Factory", "Munnar Scenic Tea Estate Walking Trail", "Mattupetty Dam"] },
  { region: "Munnar", attractions: ["Eravikulam National Park", "Anamudi Peak View", "Kundala Lake"] },
  { region: "Thekkady", attractions: ["Periyar Lake Boating & Sanctuary", "Guided Organic Spice Plantation Walk"] },
  { region: "Alleppey", attractions: ["Alleppey Backwaters & Punnamada Lake", "Private Traditional Deluxe Houseboat Cruise"] },
  { region: "Kovalam", attractions: ["Lighthouse Beach", "Hawah Beach", "Samudra Beach"] },
];

export const HIMACHAL_DAY_DEFAULTS: DayDefault[] = [
  { region: "Shimla", attractions: ["Shimla Mall Road & Ridge", "Jakhoo Temple", "Viceregal Lodge"] },
  { region: "Shimla", attractions: ["Kufri Adventure Park", "Fagu Valley View"] },
  { region: "Manali", attractions: ["Hadimba Temple", "Old Manali Cafes", "Vashisht Hot Springs"] },
  { region: "Manali", attractions: ["Solang Valley Adventure Arena", "Solang Valley Tandem Paragliding"] },
  { region: "Manali", attractions: ["Atal Tunnel & Sissu Lahaul View", "Sissu Snow Point Excursion via Atal Tunnel"] },
  { region: "Dharamshala", attractions: ["Tsuglagkhang Complex Dalai Lama Temple", "Bhagsunag Waterfall"] },
];

export const UTTARAKHAND_DAY_DEFAULTS: DayDefault[] = [
  { region: "Rishikesh", attractions: ["Triveni Ghat Evening Ganga Aarti", "Ram Jhula & Laxman Jhula", "Beatles Ashram"] },
  { region: "Rishikesh", attractions: ["16 km Ganga White Water River Rafting (Shivpuri to NIM Beach)", "Neer Garh Waterfall"] },
  { region: "Haridwar", attractions: ["Har Ki Pauri Ganga Aarti", "Mansa Devi Temple Cable Car"] },
  { region: "Jim Corbett", attractions: ["Dhikala Forest Grasslands & River Ramganga", "Exclusive Open 4x4 Gypsy Wildlife Safari"] },
  { region: "Mussoorie", attractions: ["Kempty Falls", "Mall Road Mussoorie", "Gun Hill Ropeway"] },
  { region: "Nainital", attractions: ["Naini Lake Boating", "Naina Devi Temple", "Snow View Point"] },
];

export const LADAKH_DAY_DEFAULTS: DayDefault[] = [
  { region: "Leh", attractions: ["Leh Gentle Acclimatization Walk & Market", "Leh Main Bazaar"] },
  { region: "Leh", attractions: ["Shanti Stupa Sunset & Valley Panorama", "Leh Palace", "Hall of Fame Museum"] },
  { region: "Nubra Valley", attractions: ["Khardung La Pass (5,359m Highest Motorway)", "Hunder Sand Dunes Double-Humped Camel Safari"] },
  { region: "Nubra Valley", attractions: ["Diskit Monastery & Giant Maitreya Buddha", "Sumur Sand Dunes"] },
  { region: "Pangong Tso", attractions: ["Pangong Tso High Altitude Blue Salt Lake", "Shyok River Valley Corridor"] },
  { region: "Leh", attractions: ["Chang La Pass (5,360m)", "Thiksey Monastery & Morning Prayers"] },
];

export function getDestinationDayDefaults(destination?: string): DayDefault[] {
  const d = String(destination || "").toLowerCase();
  if (d.includes("rajasthan")) return RAJASTHAN_DAY_DEFAULTS;
  if (d.includes("kashmir")) return KASHMIR_DAY_DEFAULTS;
  if (d.includes("goa")) return GOA_DAY_DEFAULTS;
  if (d.includes("kerala")) return KERALA_DAY_DEFAULTS;
  if (d.includes("himachal")) return HIMACHAL_DAY_DEFAULTS;
  if (d.includes("uttarakhand")) return UTTARAKHAND_DAY_DEFAULTS;
  if (d.includes("ladakh")) return LADAKH_DAY_DEFAULTS;
  return ANDAMAN_DAY_DEFAULTS;
}
