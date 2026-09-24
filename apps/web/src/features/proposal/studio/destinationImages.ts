/**
 * Proposal Studio — Destination Image Catalog
 * Curated Unsplash/public domain images per destination.
 * Used for "Destination Images" tab in the image changer panel.
 * No backend dependency — purely client-side.
 */

export interface DestinationImage {
  id: string;
  url: string;
  alt: string;
  label: string;
}

const ANDAMAN_IMAGES: DestinationImage[] = [
  { id: "and-1", url: "https://images.unsplash.com/photo-1589308078059-be1415eab4c3?w=800&q=80", alt: "Radhanagar Beach Havelock", label: "Radhanagar Beach" },
  { id: "and-2", url: "https://images.unsplash.com/photo-1559128010-7c1ad6e1b6a5?w=800&q=80", alt: "Crystal blue Andaman waters", label: "Andaman Waters" },
  { id: "and-3", url: "https://images.unsplash.com/photo-1570042225831-d98fa7577f1e?w=800&q=80", alt: "Tropical palm beach Andaman", label: "Tropical Beach" },
  { id: "and-4", url: "https://images.unsplash.com/photo-1583212292454-1fe6229603b7?w=800&q=80", alt: "Coral reef underwater snorkeling", label: "Coral Reef" },
  { id: "and-5", url: "https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=800&q=80", alt: "Elephant Beach Havelock Island", label: "Elephant Beach" },
  { id: "and-6", url: "https://images.unsplash.com/photo-1544551763-46a013bb70d5?w=800&q=80", alt: "Pier jetty ocean sunset", label: "Island Pier" },
];

const GOA_IMAGES: DestinationImage[] = [
  { id: "goa-1", url: "https://images.unsplash.com/photo-1512343879784-a960bf40e7f2?w=800&q=80", alt: "Goa beach sunset palm trees", label: "Goa Sunset" },
  { id: "goa-2", url: "https://images.unsplash.com/photo-1544550581-5f7ceaf7f992?w=800&q=80", alt: "Portuguese architecture Fontainhas Goa", label: "Fontainhas" },
  { id: "goa-3", url: "https://images.unsplash.com/photo-1567157577867-05ccb1388e66?w=800&q=80", alt: "Goa beach huts and ocean", label: "Beach Shacks" },
  { id: "goa-4", url: "https://images.unsplash.com/photo-1587474260584-136574528ed5?w=800&q=80", alt: "Baga beach Goa aerial", label: "Baga Beach" },
  { id: "goa-5", url: "https://images.unsplash.com/photo-1509233725247-49e657c54213?w=800&q=80", alt: "Fort Aguada Goa", label: "Fort Aguada" },
  { id: "goa-6", url: "https://images.unsplash.com/photo-1526481280693-3bfa7568e0f3?w=800&q=80", alt: "Goa palm trees tropical evening", label: "Tropical Evening" },
];

const RAJASTHAN_IMAGES: DestinationImage[] = [
  { id: "raj-1", url: "https://images.unsplash.com/photo-1524492412937-b28074a5d7da?w=800&q=80", alt: "Amber Fort Jaipur Rajasthan", label: "Amber Fort" },
  { id: "raj-2", url: "https://images.unsplash.com/photo-1477587458883-47145ed31769?w=800&q=80", alt: "Mehrangarh Fort Jodhpur blue city", label: "Mehrangarh Fort" },
  { id: "raj-3", url: "https://images.unsplash.com/photo-1599661046289-e31897846e41?w=800&q=80", alt: "Jaisalmer golden fort desert", label: "Jaisalmer Fort" },
  { id: "raj-4", url: "https://images.unsplash.com/photo-1603262110263-fb0112e7cc33?w=800&q=80", alt: "Udaipur City Palace lake", label: "Udaipur Palace" },
  { id: "raj-5", url: "https://images.unsplash.com/photo-1578662996442-48f60103fc96?w=800&q=80", alt: "Sam sand dunes camel Rajasthan", label: "Sand Dunes" },
  { id: "raj-6", url: "https://images.unsplash.com/photo-1568454537842-d933259bb258?w=800&q=80", alt: "Hawa Mahal Jaipur pink facade", label: "Hawa Mahal" },
];

const KERALA_IMAGES: DestinationImage[] = [
  { id: "ker-1", url: "https://images.unsplash.com/photo-1602216056096-3b40cc0c9944?w=800&q=80", alt: "Alleppey Kerala backwaters houseboat", label: "Backwaters" },
  { id: "ker-2", url: "https://images.unsplash.com/photo-1595901395225-a5d30be7dc9c?w=800&q=80", alt: "Munnar green tea estates", label: "Munnar Tea" },
  { id: "ker-3", url: "https://images.unsplash.com/photo-1531600143516-cf56f1f6c96b?w=800&q=80", alt: "Chinese fishing nets Fort Kochi Kerala", label: "Kochi Nets" },
  { id: "ker-4", url: "https://images.unsplash.com/photo-1567321938631-54b3fd8aaa29?w=800&q=80", alt: "Kovalam lighthouse beach Kerala", label: "Kovalam Beach" },
  { id: "ker-5", url: "https://images.unsplash.com/photo-1506461883276-594a12b5bca3?w=800&q=80", alt: "Periyar tiger reserve Thekkady", label: "Periyar Lake" },
  { id: "ker-6", url: "https://images.unsplash.com/photo-1591159228893-f4b11e1a6e11?w=800&q=80", alt: "Kerala tropical waterfall lush forest", label: "Kerala Waterfall" },
];

const KASHMIR_IMAGES: DestinationImage[] = [
  { id: "kas-1", url: "https://images.unsplash.com/photo-1558618666-fcd25c85cd64?w=800&q=80", alt: "Dal Lake Srinagar Kashmir shikara boats", label: "Dal Lake" },
  { id: "kas-2", url: "https://images.unsplash.com/photo-1631378783099-04c8c2e64bd4?w=800&q=80", alt: "Gulmarg ski slopes snowcapped mountains", label: "Gulmarg Snow" },
  { id: "kas-3", url: "https://images.unsplash.com/photo-1618137306611-adfd4fc5fb01?w=800&q=80", alt: "Pahalgam Betaab Valley green meadows", label: "Pahalgam Valley" },
  { id: "kas-4", url: "https://images.unsplash.com/photo-1566024287286-457247b70310?w=800&q=80", alt: "Sonamarg glacier Kashmir mountain", label: "Sonamarg Glacier" },
  { id: "kas-5", url: "https://images.unsplash.com/photo-1609766418204-3e43ee41a25e?w=800&q=80", alt: "Mughal gardens Srinagar Kashmir", label: "Mughal Gardens" },
  { id: "kas-6", url: "https://images.unsplash.com/photo-1574236170878-f2f2e3985ca1?w=800&q=80", alt: "Shankaracharya temple hill Srinagar", label: "Shankaracharya" },
];

const HIMACHAL_IMAGES: DestinationImage[] = [
  { id: "him-1", url: "https://images.unsplash.com/photo-1626621341517-bbf3d9990a23?w=800&q=80", alt: "Shimla hill station colonial architecture", label: "Shimla" },
  { id: "him-2", url: "https://images.unsplash.com/photo-1610543688127-46c00fba16e4?w=800&q=80", alt: "Manali Hadimba temple snowy mountains", label: "Manali Hadimba" },
  { id: "him-3", url: "https://images.unsplash.com/photo-1529963183134-61a90db47eaf?w=800&q=80", alt: "Solang Valley Manali snow adventure", label: "Solang Valley" },
  { id: "him-4", url: "https://images.unsplash.com/photo-1546961342-ea5f62d4f5cb?w=800&q=80", alt: "Spiti Valley mountain desert", label: "Spiti Valley" },
  { id: "him-5", url: "https://images.unsplash.com/photo-1596777404618-fe47a0cd5c28?w=800&q=80", alt: "Dharamshala McLeod Ganj", label: "Dharamshala" },
  { id: "him-6", url: "https://images.unsplash.com/photo-1570974907979-f842d1f6ef58?w=800&q=80", alt: "Himachal Pradesh mountain peaks green valley", label: "Himachal Valley" },
];

const UTTARAKHAND_IMAGES: DestinationImage[] = [
  { id: "utt-1", url: "https://images.unsplash.com/photo-1616401784845-180882ba9ba8?w=800&q=80", alt: "Rishikesh Ram Jhula bridge Ganga", label: "Rishikesh Jhula" },
  { id: "utt-2", url: "https://images.unsplash.com/photo-1569534403429-2553c85f1acb?w=800&q=80", alt: "Haridwar Ganga aarti evening ghats", label: "Haridwar Aarti" },
  { id: "utt-3", url: "https://images.unsplash.com/photo-1567472863279-6f05b2da4b6f?w=800&q=80", alt: "Jim Corbett tiger national park", label: "Corbett Safari" },
  { id: "utt-4", url: "https://images.unsplash.com/photo-1567784177951-6fa58317e16b?w=800&q=80", alt: "Mussoorie Mall Road hill station", label: "Mussoorie" },
  { id: "utt-5", url: "https://images.unsplash.com/photo-1571127236794-81c0bbfe1ce3?w=800&q=80", alt: "Nainital lake boat mountain", label: "Nainital Lake" },
  { id: "utt-6", url: "https://images.unsplash.com/photo-1584551246679-0daf3d275d0f?w=800&q=80", alt: "Rishikesh white water river rafting", label: "River Rafting" },
];

const LADAKH_IMAGES: DestinationImage[] = [
  { id: "lad-1", url: "https://images.unsplash.com/photo-1564670874-e1f6ece4f6db?w=800&q=80", alt: "Pangong Tso Lake Ladakh blue sky", label: "Pangong Lake" },
  { id: "lad-2", url: "https://images.unsplash.com/photo-1597171629737-8c85f8f69dc6?w=800&q=80", alt: "Leh Palace Ladakh mountain monastery", label: "Leh Palace" },
  { id: "lad-3", url: "https://images.unsplash.com/photo-1601823984263-73eacad22d16?w=800&q=80", alt: "Nubra Valley Hunder sand dunes camel", label: "Nubra Dunes" },
  { id: "lad-4", url: "https://images.unsplash.com/photo-1589474135969-e6df3e1b9c5b?w=800&q=80", alt: "Khardung La Pass Ladakh high altitude", label: "Khardung La" },
  { id: "lad-5", url: "https://images.unsplash.com/photo-1596886985523-bc7a4a0aa6dc?w=800&q=80", alt: "Diskit Monastery Buddha statue Nubra", label: "Diskit Monastery" },
  { id: "lad-6", url: "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?w=800&q=80", alt: "Thiksey Monastery morning light Ladakh", label: "Thiksey Monastery" },
];

const PUNJAB_IMAGES: DestinationImage[] = [
  { id: "pun-1", url: "https://images.unsplash.com/photo-1602861764949-c3f29eb9c38b?w=800&q=80", alt: "Golden Temple Amritsar Harmandir Sahib", label: "Golden Temple" },
  { id: "pun-2", url: "https://images.unsplash.com/photo-1614484478126-9fbc28be3c8c?w=800&q=80", alt: "Wagah border ceremony Amritsar", label: "Wagah Border" },
  { id: "pun-3", url: "https://images.unsplash.com/photo-1591154669695-5f2a8d20c089?w=800&q=80", alt: "Punjab fields mustard yellow landscape", label: "Mustard Fields" },
  { id: "pun-4", url: "https://images.unsplash.com/photo-1590322016949-9a9a2e3d27e0?w=800&q=80", alt: "Jallianwala Bagh memorial garden Amritsar", label: "Jallianwala Bagh" },
  { id: "pun-5", url: "https://images.unsplash.com/photo-1555400038-63f5ba517a47?w=800&q=80", alt: "Punjabi food langar thali feast", label: "Punjab Cuisine" },
  { id: "pun-6", url: "https://images.unsplash.com/photo-1574236170878-f2f2e3985ca1?w=800&q=80", alt: "Chandigarh Rock Garden sculpture", label: "Rock Garden" },
];

const GENERIC_INDIA_IMAGES: DestinationImage[] = [
  { id: "gen-1", url: "https://images.unsplash.com/photo-1524492412937-b28074a5d7da?w=800&q=80", alt: "India luxury travel palace", label: "Luxury India" },
  { id: "gen-2", url: "https://images.unsplash.com/photo-1598091383021-15ddea10925d?w=800&q=80", alt: "India tropical beach paradise", label: "Beach Paradise" },
  { id: "gen-3", url: "https://images.unsplash.com/photo-1544735716-392fe2489ffa?w=800&q=80", alt: "India mountain landscape scenic", label: "Mountains" },
  { id: "gen-4", url: "https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=800&q=80", alt: "Scenic sunrise India", label: "Sunrise" },
  { id: "gen-5", url: "https://images.unsplash.com/photo-1587474260584-136574528ed5?w=800&q=80", alt: "Aerial coastal India", label: "Coastal India" },
  { id: "gen-6", url: "https://images.unsplash.com/photo-1582966772680-860e372bb558?w=800&q=80", alt: "India heritage cultural site", label: "India Heritage" },
];

export function getDestinationImages(destination?: string): DestinationImage[] {
  const d = String(destination || "").toLowerCase();
  if (d.includes("andaman")) return ANDAMAN_IMAGES;
  if (d.includes("goa")) return GOA_IMAGES;
  if (d.includes("rajasthan")) return RAJASTHAN_IMAGES;
  if (d.includes("kerala")) return KERALA_IMAGES;
  if (d.includes("kashmir") || d.includes("jammu")) return KASHMIR_IMAGES;
  if (d.includes("himachal")) return HIMACHAL_IMAGES;
  if (d.includes("uttarakhand")) return UTTARAKHAND_IMAGES;
  if (d.includes("ladakh")) return LADAKH_IMAGES;
  if (d.includes("punjab")) return PUNJAB_IMAGES;
  return GENERIC_INDIA_IMAGES;
}
