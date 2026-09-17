"use client";

import React, { useState } from "react";

interface Campaign {
  id: string;
  title: string;
  package: string;
  channel: "whatsapp" | "instagram" | "email" | "all";
  status: "active" | "scheduled" | "completed";
  reach: number;
  leads: number;
  discount: string;
  startDate: string;
  endDate: string;
  highlight: string;
}

const INITIAL_CAMPAIGNS: Campaign[] = [
  {
    id: "camp-1",
    title: "Diwali Island Getaway 2026",
    package: "5D/4N Havelock & Neil Luxury Escape",
    channel: "all",
    status: "active",
    reach: 14200,
    leads: 32,
    discount: "15% OFF",
    startDate: "2026-09-01",
    endDate: "2026-10-15",
    highlight: "Complimentary Scuba Dive & Candlelight Dinner at Symphony Palms",
  },
  {
    id: "camp-2",
    title: "Honeymoon Sunset Cruise Special",
    package: "6D/5N Port Blair & Havelock Romance Tour",
    channel: "whatsapp",
    status: "active",
    reach: 8900,
    leads: 24,
    discount: "₹5,000 Flat OFF",
    startDate: "2026-09-05",
    endDate: "2026-10-30",
    highlight: "Private Speedboat transfer + Beachside Flower Bed Setup",
  },
  {
    id: "camp-3",
    title: "Monsoon Serenity Scuba Blast",
    package: "4D/3N Elephant Beach & Coral Safari",
    channel: "instagram",
    status: "scheduled",
    reach: 5400,
    leads: 18,
    discount: "10% OFF",
    startDate: "2026-10-01",
    endDate: "2026-11-15",
    highlight: "PADI Certified Dive Instructor + GoPro 4K Underwater Video",
  },
];

const PROMO_PACKAGES = [
  {
    id: "pkg-1",
    name: "Luxury Havelock & Neil Island Odyssey",
    duration: "5 Days / 4 Nights",
    startingPrice: "₹38,000 / couple",
    resort: "Symphony Palms Beach Resort / Taj Exotica",
    tags: ["Best Seller", "Couples & Family"],
    description: "Private transfers, cruise tickets on Makruzz/Nautika, sunset at Radhanagar Beach, and private beach dinner.",
    messageText: `🌴 *Darun Tourism Exclusive - Luxury Andaman Getaway* 🌴\n\n✨ Experience 5 Days / 4 Nights in Havelock & Neil Island.\n🛎️ Stay at premium beach villas with ocean views.\n🚤 Private ferry transfers via Nautika/Makruzz.\n🤿 Complimentary snorkeling & sunset dining!\n\nSpecial Festival Offer: Use Code *DARUNLUXURY* for 15% OFF.\nBook your bespoke itinerary now with Darun Tourism!`,
  },
  {
    id: "pkg-2",
    name: "Andaman Adventure & Coral Explorer",
    duration: "6 Days / 5 Nights",
    startingPrice: "₹45,000 / couple",
    resort: "Seashell Havelock & Coral Reef Neil",
    tags: ["Adventure", "Scuba & Trekking"],
    description: "Includes PADI Discovery Scuba at Nemo Reef, Sea Walk at Elephant Beach, and Baratang Limestone Caves trek.",
    messageText: `🌊 *Underwater Adventure in the Andamans with Darun Tourism* 🐠\n\n6D/5N of crystal-clear turquoise waters & coral reefs!\n✔️ Discover Scuba Diving with underwater 4K video\n✔️ Jet Ski & Banana Ride at Elephant Beach\n✔️ Luxury island stays & curated dining\n\nLimited slots available. Reply 'DETAILS' to get your personalized plan!`,
  },
  {
    id: "pkg-3",
    name: "Signature Port Blair & Island Romance",
    duration: "4 Days / 3 Nights",
    startingPrice: "₹29,000 / couple",
    resort: "Sinclairs Bayview Port Blair",
    tags: ["Weekend Special", "Romantic Escape"],
    description: "Cellular Jail light & sound show VIP seats, Corbyn's Cove sunset, and Chidiyatapu bird sanctuary.",
    messageText: `🌅 *Romantic Weekend Escape to the Andamans* 🥂\n\nCurated 4D/3N quick getaway by Darun Tourism.\nIndulge in private oceanfront suites, candlelit dinners, and serene sunset cruises.\n\nExclusive discount code *ROMANCE26* gives flat ₹4,000 off this week!`,
  },
];

const COUPONS = [
  { code: "DARUNVIP15", discount: "15% OFF", desc: "For bookings above ₹1,00,000", used: 14, expiry: "31 Oct 2026", active: true },
  { code: "EARLYISLAND", discount: "₹5,000 OFF", desc: "Advance booking (30+ days prior)", used: 22, expiry: "15 Nov 2026", active: true },
  { code: "HONEYMOON26", discount: "10% OFF", desc: "Includes free candlelight dinner setup", used: 9, expiry: "31 Dec 2026", active: true },
  { code: "MONSOONBLISS", discount: "₹3,500 OFF", desc: "Off-peak luxury travel packages", used: 18, expiry: "20 Oct 2026", active: true },
];

export function MarketingHub() {
  const [activeTab, setActiveTab] = useState<"campaigns" | "packages" | "broadcast" | "coupons">("campaigns");
  const [campaigns, setCampaigns] = useState<Campaign[]>(INITIAL_CAMPAIGNS);
  const [copiedCode, setCopiedCode] = useState<string | null>(null);
  const [toastMessage, setToastMessage] = useState<string | null>(null);

  // New Campaign Modal state
  const [showNewModal, setShowNewModal] = useState(false);
  const [newTitle, setNewTitle] = useState("");
  const [newPackage, setNewPackage] = useState("");
  const [newChannel, setNewChannel] = useState<"whatsapp" | "instagram" | "email" | "all">("all");
  const [newDiscount, setNewDiscount] = useState("15% OFF");
  const [newHighlight, setNewHighlight] = useState("");

  // Broadcast modal/state
  const [broadcastTarget, setBroadcastTarget] = useState<"leads" | "clients" | "all">("leads");
  const [broadcastText, setBroadcastText] = useState(
    `🌴 *Exclusive Andaman Travel Offer from Darun Tourism* 🌴\n\nPlan your dream tropical vacation with our customized luxury itineraries!\n✨ 15% discount with promo code *DARUNVIP15*\n🌊 Private beachfront resorts & luxury ferries included.\n\nReply to this message or call our travel expert to design your trip!`
  );

  const showToast = (msg: string) => {
    setToastMessage(msg);
    setTimeout(() => setToastMessage(null), 3500);
  };

  const handleCopy = (text: string, label: string) => {
    navigator.clipboard.writeText(text);
    setCopiedCode(label);
    showToast(`Copied "${label}" to clipboard!`);
    setTimeout(() => setCopiedCode(null), 2500);
  };

  const handleSendWhatsApp = (text: string) => {
    const encoded = encodeURIComponent(text);
    window.open(`https://wa.me/?text=${encoded}`, "_blank");
  };

  const handleCreateCampaign = (e: React.FormEvent) => {
    e.preventDefault();
    if (!newTitle.trim()) return;

    const newCamp: Campaign = {
      id: `camp-${Date.now()}`,
      title: newTitle.trim(),
      package: newPackage.trim() || "Andaman Bespoke Tour",
      channel: newChannel,
      status: "active",
      reach: 0,
      leads: 0,
      discount: newDiscount.trim() || "Special Offer",
      startDate: new Date().toISOString().split("T")[0],
      endDate: "2026-11-30",
      highlight: newHighlight.trim() || "Luxury island stays & private tours",
    };

    setCampaigns([newCamp, ...campaigns]);
    setShowNewModal(false);
    setNewTitle("");
    setNewPackage("");
    setNewHighlight("");
    showToast("Marketing Campaign created successfully!");
  };

  return (
    <div className="page active animate-in fade-in slide-in-from-bottom-4 duration-500" style={{ padding: "0 0 60px 0" }}>
      {/* Toast Notification */}
      {toastMessage && (
        <div
          style={{
            position: "fixed",
            bottom: "24px",
            right: "24px",
            backgroundColor: "#1b1d24",
            border: "1px solid var(--gold)",
            color: "var(--gold)",
            padding: "12px 20px",
            borderRadius: "10px",
            boxShadow: "0 10px 30px rgba(0,0,0,0.5)",
            zIndex: 9999,
            display: "flex",
            alignItems: "center",
            gap: "10px",
            fontSize: "13px",
            fontWeight: 500,
          }}
          className="animate-in fade-in slide-in-from-bottom-2 duration-200"
        >
          <i className="ti ti-check" style={{ fontSize: "16px" }} />
          <span>{toastMessage}</span>
        </div>
      )}

      {/* Header */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "28px", flexWrap: "wrap", gap: "16px" }}>
        <div>
          <div style={{ display: "flex", alignItems: "center", gap: "10px", marginBottom: "6px" }}>
            <span
              style={{
                width: "32px",
                height: "32px",
                borderRadius: "8px",
                background: "linear-gradient(135deg, rgba(212,175,55,0.2), rgba(212,175,55,0.05))",
                border: "1px solid rgba(212,175,55,0.3)",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                color: "var(--gold)",
                fontSize: "16px",
              }}
            >
              <i className="ti ti-speakerphone" />
            </span>
            <h1 style={{ fontSize: "24px", fontWeight: 700, margin: 0 }}>Marketing & Campaigns</h1>
          </div>
          <p style={{ color: "var(--text-dim)", fontSize: "13.5px", margin: 0 }}>
            Launch luxury Andaman promotions, broadcast WhatsApp offers to leads, and drive new high-value bookings.
          </p>
        </div>

        <div style={{ display: "flex", gap: "12px" }}>
          <button
            className="btn-gold"
            style={{ display: "flex", alignItems: "center", gap: "8px", fontSize: "13px", padding: "9px 16px", cursor: "pointer" }}
            onClick={() => setShowNewModal(true)}
          >
            <i className="ti ti-plus" />
            <span>New Campaign</span>
          </button>
          <button
            style={{
              display: "flex",
              alignItems: "center",
              gap: "8px",
              fontSize: "13px",
              padding: "9px 16px",
              backgroundColor: "rgba(37, 211, 102, 0.12)",
              border: "1px solid rgba(37, 211, 102, 0.3)",
              color: "#25D366",
              borderRadius: "10px",
              fontWeight: 600,
              cursor: "pointer",
              transition: "all 0.15s ease",
            }}
            onClick={() => setActiveTab("broadcast")}
          >
            <i className="ti ti-brand-whatsapp" style={{ fontSize: "16px" }} />
            <span>WhatsApp Broadcast</span>
          </button>
        </div>
      </div>

      {/* KPI Stats Row */}
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))",
          gap: "16px",
          marginBottom: "28px",
        }}
      >
        <div className="card" style={{ padding: "20px" }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "10px" }}>
            <span style={{ fontSize: "11.5px", textTransform: "uppercase", letterSpacing: "0.5px", color: "var(--text-faint)", fontWeight: 600 }}>
              Total Audience Reach
            </span>
            <span style={{ fontSize: "11px", color: "var(--green)", backgroundColor: "rgba(63,191,127,0.1)", padding: "2px 8px", borderRadius: "12px", fontWeight: 600 }}>
              +24.5% MoM
            </span>
          </div>
          <div style={{ fontSize: "26px", fontWeight: 700, color: "var(--foreground)", fontFamily: "var(--font-heading)" }}>
            28,500<span style={{ fontSize: "16px", fontWeight: 500, color: "var(--text-faint)" }}> travelers</span>
          </div>
          <div style={{ fontSize: "12px", color: "var(--text-dim)", marginTop: "6px" }}>
            Across WhatsApp blasts & Instagram promos
          </div>
        </div>

        <div className="card" style={{ padding: "20px" }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "10px" }}>
            <span style={{ fontSize: "11.5px", textTransform: "uppercase", letterSpacing: "0.5px", color: "var(--text-faint)", fontWeight: 600 }}>
              Inquiries & Leads Generated
            </span>
            <span style={{ fontSize: "11px", color: "var(--gold)", backgroundColor: "rgba(212,175,55,0.1)", padding: "2px 8px", borderRadius: "12px", fontWeight: 600 }}>
              5.1% Conv.
            </span>
          </div>
          <div style={{ fontSize: "26px", fontWeight: 700, color: "var(--foreground)", fontFamily: "var(--font-heading)" }}>
            74<span style={{ fontSize: "16px", fontWeight: 500, color: "var(--text-faint)" }}> leads</span>
          </div>
          <div style={{ fontSize: "12px", color: "var(--text-dim)", marginTop: "6px" }}>
            Converted directly into CRM pipeline
          </div>
        </div>

        <div className="card" style={{ padding: "20px" }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "10px" }}>
            <span style={{ fontSize: "11.5px", textTransform: "uppercase", letterSpacing: "0.5px", color: "var(--text-faint)", fontWeight: 600 }}>
              Active Promotions
            </span>
            <span style={{ fontSize: "11px", color: "#60a5fa", backgroundColor: "rgba(96,165,250,0.1)", padding: "2px 8px", borderRadius: "12px", fontWeight: 600 }}>
              Live
            </span>
          </div>
          <div style={{ fontSize: "26px", fontWeight: 700, color: "var(--foreground)", fontFamily: "var(--font-heading)" }}>
            {campaigns.filter((c) => c.status === "active").length} Live
            <span style={{ fontSize: "15px", fontWeight: 500, color: "var(--text-faint)", marginLeft: "8px" }}>
              ({campaigns.length} total)
            </span>
          </div>
          <div style={{ fontSize: "12px", color: "var(--text-dim)", marginTop: "6px" }}>
            Diwali & Honeymoon seasons running
          </div>
        </div>

        <div className="card" style={{ padding: "20px" }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "10px" }}>
            <span style={{ fontSize: "11.5px", textTransform: "uppercase", letterSpacing: "0.5px", color: "var(--text-faint)", fontWeight: 600 }}>
              Pipeline Value Driven
            </span>
            <span style={{ fontSize: "11px", color: "var(--green)", backgroundColor: "rgba(63,191,127,0.1)", padding: "2px 8px", borderRadius: "12px", fontWeight: 600 }}>
              High ROI
            </span>
          </div>
          <div style={{ fontSize: "26px", fontWeight: 700, color: "var(--gold)", fontFamily: "var(--font-heading)" }}>
            ₹7,20,000
          </div>
          <div style={{ fontSize: "12px", color: "var(--text-dim)", marginTop: "6px" }}>
            From recent promotional campaigns
          </div>
        </div>
      </div>

      {/* Navigation Tabs */}
      <div
        style={{
          display: "flex",
          borderBottom: "1px solid var(--line-soft)",
          marginBottom: "24px",
          gap: "8px",
        }}
      >
        <button
          onClick={() => setActiveTab("campaigns")}
          style={{
            padding: "10px 18px",
            fontSize: "13.5px",
            fontWeight: 600,
            background: "none",
            border: "none",
            borderBottom: activeTab === "campaigns" ? "2px solid var(--gold)" : "2px solid transparent",
            color: activeTab === "campaigns" ? "var(--gold)" : "var(--text-dim)",
            cursor: "pointer",
            display: "flex",
            alignItems: "center",
            gap: "8px",
          }}
        >
          <i className="ti ti-ad-2" />
          <span>Active Campaigns ({campaigns.length})</span>
        </button>

        <button
          onClick={() => setActiveTab("broadcast")}
          style={{
            padding: "10px 18px",
            fontSize: "13.5px",
            fontWeight: 600,
            background: "none",
            border: "none",
            borderBottom: activeTab === "broadcast" ? "2px solid var(--gold)" : "2px solid transparent",
            color: activeTab === "broadcast" ? "var(--gold)" : "var(--text-dim)",
            cursor: "pointer",
            display: "flex",
            alignItems: "center",
            gap: "8px",
          }}
        >
          <i className="ti ti-brand-whatsapp" />
          <span>WhatsApp Broadcast</span>
        </button>

        <button
          onClick={() => setActiveTab("packages")}
          style={{
            padding: "10px 18px",
            fontSize: "13.5px",
            fontWeight: 600,
            background: "none",
            border: "none",
            borderBottom: activeTab === "packages" ? "2px solid var(--gold)" : "2px solid transparent",
            color: activeTab === "packages" ? "var(--gold)" : "var(--text-dim)",
            cursor: "pointer",
            display: "flex",
            alignItems: "center",
            gap: "8px",
          }}
        >
          <i className="ti ti-compass" />
          <span>Ready Promo Packages ({PROMO_PACKAGES.length})</span>
        </button>

        <button
          onClick={() => setActiveTab("coupons")}
          style={{
            padding: "10px 18px",
            fontSize: "13.5px",
            fontWeight: 600,
            background: "none",
            border: "none",
            borderBottom: activeTab === "coupons" ? "2px solid var(--gold)" : "2px solid transparent",
            color: activeTab === "coupons" ? "var(--gold)" : "var(--text-dim)",
            cursor: "pointer",
            display: "flex",
            alignItems: "center",
            gap: "8px",
          }}
        >
          <i className="ti ti-ticket" />
          <span>Coupons & Codes ({COUPONS.length})</span>
        </button>
      </div>

      {/* Tab Content: CAMPAIGNS */}
      {activeTab === "campaigns" && (
        <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
          {campaigns.map((camp) => (
            <div
              key={camp.id}
              className="card"
              style={{
                padding: "20px 24px",
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
                flexWrap: "wrap",
                gap: "20px",
                borderLeft: camp.status === "active" ? "4px solid var(--gold)" : "4px solid var(--text-faint)",
              }}
            >
              <div style={{ flex: "1 1 320px" }}>
                <div style={{ display: "flex", alignItems: "center", gap: "10px", marginBottom: "6px" }}>
                  <h3 style={{ fontSize: "16px", fontWeight: 600, margin: 0, color: "var(--foreground)" }}>{camp.title}</h3>
                  <span
                    style={{
                      fontSize: "11px",
                      padding: "2px 8px",
                      borderRadius: "12px",
                      fontWeight: 600,
                      backgroundColor:
                        camp.status === "active"
                          ? "rgba(63,191,127,0.12)"
                          : "rgba(255,255,255,0.06)",
                      color: camp.status === "active" ? "var(--green)" : "var(--text-faint)",
                      textTransform: "capitalize",
                    }}
                  >
                    {camp.status}
                  </span>
                  <span
                    style={{
                      fontSize: "11px",
                      padding: "2px 8px",
                      borderRadius: "6px",
                      fontWeight: 600,
                      backgroundColor: "rgba(212,175,55,0.1)",
                      color: "var(--gold)",
                      border: "1px solid rgba(212,175,55,0.2)",
                    }}
                  >
                    {camp.discount}
                  </span>
                </div>

                <div style={{ fontSize: "13px", color: "var(--text-dim)", marginBottom: "8px" }}>
                  📦 <strong style={{ color: "var(--foreground)" }}>{camp.package}</strong>
                </div>

                <div style={{ fontSize: "12px", color: "var(--text-faint)", display: "flex", gap: "16px", flexWrap: "wrap" }}>
                  <span>
                    <i className="ti ti-sparkles" style={{ color: "var(--gold)", marginRight: "4px" }} />
                    {camp.highlight}
                  </span>
                  <span>
                    <i className="ti ti-calendar" style={{ marginRight: "4px" }} />
                    {camp.startDate} to {camp.endDate}
                  </span>
                </div>
              </div>

              {/* Metrics & Action */}
              <div style={{ display: "flex", alignItems: "center", gap: "24px" }}>
                <div style={{ textAlign: "right" }}>
                  <div style={{ fontSize: "11px", color: "var(--text-faint)", textTransform: "uppercase" }}>Reach</div>
                  <div style={{ fontSize: "16px", fontWeight: 700, color: "var(--foreground)" }}>
                    {camp.reach.toLocaleString()}
                  </div>
                </div>

                <div style={{ textAlign: "right" }}>
                  <div style={{ fontSize: "11px", color: "var(--text-faint)", textTransform: "uppercase" }}>Leads</div>
                  <div style={{ fontSize: "16px", fontWeight: 700, color: "var(--gold)" }}>
                    +{camp.leads}
                  </div>
                </div>

                <div style={{ display: "flex", gap: "8px" }}>
                  <button
                    onClick={() => {
                      const msg = `🌟 *${camp.title}* with Darun Tourism!\n\n${camp.package}\nOffer: *${camp.discount}*\n✨ ${camp.highlight}\n\nContact us today to book your island holiday!`;
                      handleSendWhatsApp(msg);
                    }}
                    style={{
                      padding: "8px 12px",
                      backgroundColor: "rgba(37, 211, 102, 0.12)",
                      border: "1px solid rgba(37, 211, 102, 0.3)",
                      color: "#25D366",
                      borderRadius: "8px",
                      fontSize: "12px",
                      fontWeight: 600,
                      cursor: "pointer",
                      display: "flex",
                      alignItems: "center",
                      gap: "6px",
                    }}
                    title="Broadcast on WhatsApp"
                  >
                    <i className="ti ti-brand-whatsapp" />
                    <span>Broadcast</span>
                  </button>

                  <button
                    onClick={() => {
                      const msg = `🌟 ${camp.title} - ${camp.package} (${camp.discount})\n${camp.highlight}`;
                      handleCopy(msg, camp.title);
                    }}
                    style={{
                      padding: "8px 12px",
                      backgroundColor: "var(--surface)",
                      border: "1px solid var(--line-soft)",
                      color: "var(--text-dim)",
                      borderRadius: "8px",
                      fontSize: "12px",
                      cursor: "pointer",
                      display: "flex",
                      alignItems: "center",
                      gap: "6px",
                    }}
                    title="Copy Campaign Summary"
                  >
                    <i className="ti ti-copy" />
                    <span>{copiedCode === camp.title ? "Copied!" : "Copy"}</span>
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Tab Content: WHATSAPP BROADCAST */}
      {activeTab === "broadcast" && (
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(360px, 1fr))", gap: "20px" }}>
          <div className="card" style={{ padding: "24px" }}>
            <h3 style={{ fontSize: "16px", fontWeight: 600, marginBottom: "6px", display: "flex", alignItems: "center", gap: "8px" }}>
              <i className="ti ti-brand-whatsapp" style={{ color: "#25D366", fontSize: "20px" }} />
              Compose WhatsApp Promotional Broadcast
            </h3>
            <p style={{ fontSize: "12.5px", color: "var(--text-dim)", marginBottom: "20px" }}>
              Send targeted promotional travel messages and discount codes directly to your clients or leads list.
            </p>

            <div style={{ marginBottom: "16px" }}>
              <label style={{ fontSize: "12px", fontWeight: 600, color: "var(--text-faint)", display: "block", marginBottom: "6px" }}>
                TARGET AUDIENCE
              </label>
              <div style={{ display: "flex", gap: "10px" }}>
                {(["leads", "clients", "all"] as const).map((t) => (
                  <button
                    key={t}
                    type="button"
                    onClick={() => setBroadcastTarget(t)}
                    style={{
                      flex: 1,
                      padding: "8px 12px",
                      borderRadius: "8px",
                      fontSize: "12.5px",
                      fontWeight: 500,
                      cursor: "pointer",
                      border: broadcastTarget === t ? "1px solid var(--gold)" : "1px solid var(--line-soft)",
                      backgroundColor: broadcastTarget === t ? "rgba(212,175,55,0.12)" : "var(--surface)",
                      color: broadcastTarget === t ? "var(--gold)" : "var(--text-dim)",
                      textTransform: "capitalize",
                    }}
                  >
                    {t === "all" ? "All Contacts" : t}
                  </button>
                ))}
              </div>
            </div>

            <div style={{ marginBottom: "20px" }}>
              <label style={{ fontSize: "12px", fontWeight: 600, color: "var(--text-faint)", display: "block", marginBottom: "6px" }}>
                MESSAGE TEMPLATE (MARKDOWN FORMATTED)
              </label>
              <textarea
                rows={8}
                value={broadcastText}
                onChange={(e) => setBroadcastText(e.target.value)}
                style={{
                  width: "100%",
                  padding: "12px",
                  borderRadius: "8px",
                  backgroundColor: "var(--surface)",
                  border: "1px solid var(--line-soft)",
                  color: "var(--foreground)",
                  fontSize: "13px",
                  fontFamily: "inherit",
                  resize: "vertical",
                  boxSizing: "border-box",
                }}
              />
            </div>

            <div style={{ display: "flex", gap: "12px" }}>
              <button
                className="btn-gold"
                style={{
                  flex: 1,
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  gap: "8px",
                  padding: "12px",
                  fontSize: "13px",
                  cursor: "pointer",
                  backgroundColor: "#25D366",
                  color: "#0F1117",
                  border: "none",
                  fontWeight: 700,
                }}
                onClick={() => handleSendWhatsApp(broadcastText)}
              >
                <i className="ti ti-send" style={{ fontSize: "16px" }} />
                <span>Open WhatsApp Broadcast</span>
              </button>

              <button
                style={{
                  padding: "12px 18px",
                  backgroundColor: "var(--surface)",
                  border: "1px solid var(--line-soft)",
                  color: "var(--text-dim)",
                  borderRadius: "8px",
                  fontSize: "13px",
                  cursor: "pointer",
                }}
                onClick={() => handleCopy(broadcastText, "Broadcast Template")}
              >
                <i className="ti ti-copy" style={{ marginRight: "6px" }} />
                <span>Copy</span>
              </button>
            </div>
          </div>

          {/* Live Mobile WhatsApp Preview */}
          <div className="card" style={{ padding: "24px" }}>
            <h4 style={{ fontSize: "13px", color: "var(--text-faint)", textTransform: "uppercase", letterSpacing: "0.5px", marginBottom: "16px" }}>
              WhatsApp Message Preview
            </h4>

            <div
              style={{
                backgroundColor: "#0b141a",
                borderRadius: "16px",
                border: "1px solid #222d34",
                padding: "20px",
                maxWidth: "380px",
                margin: "0 auto",
                boxShadow: "0 10px 25px rgba(0,0,0,0.4)",
              }}
            >
              <div style={{ display: "flex", alignItems: "center", gap: "10px", marginBottom: "14px", borderBottom: "1px solid #1f2c34", paddingBottom: "10px" }}>
                <div style={{ width: "32px", height: "32px", borderRadius: "50%", backgroundColor: "var(--gold)", color: "#000", display: "flex", alignItems: "center", justifyContent: "center", fontWeight: 700, fontSize: "14px" }}>
                  D
                </div>
                <div>
                  <div style={{ fontSize: "13px", fontWeight: 600, color: "#e9edef" }}>Darun Tourism Official</div>
                  <div style={{ fontSize: "10.5px", color: "#8696a0" }}>Verified Business Account</div>
                </div>
              </div>

              <div
                style={{
                  backgroundColor: "#005c4b",
                  borderRadius: "8px 8px 0 8px",
                  padding: "12px 14px",
                  color: "#e9edef",
                  fontSize: "12.5px",
                  lineHeight: "1.5",
                  whiteSpace: "pre-wrap",
                  wordBreak: "break-word",
                }}
              >
                {broadcastText}
                <div style={{ textAlign: "right", fontSize: "10px", color: "rgba(255,255,255,0.6)", marginTop: "6px" }}>
                  10:30 AM ✓✓
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Tab Content: PROMO PACKAGES */}
      {activeTab === "packages" && (
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(320px, 1fr))", gap: "20px" }}>
          {PROMO_PACKAGES.map((pkg) => (
            <div key={pkg.id} className="card" style={{ padding: "24px", display: "flex", flexDirection: "column" }}>
              <div style={{ display: "flex", gap: "6px", marginBottom: "10px", flexWrap: "wrap" }}>
                {pkg.tags.map((tag) => (
                  <span
                    key={tag}
                    style={{
                      fontSize: "10.5px",
                      padding: "2px 8px",
                      borderRadius: "12px",
                      backgroundColor: "rgba(212,175,55,0.12)",
                      color: "var(--gold)",
                      fontWeight: 600,
                    }}
                  >
                    {tag}
                  </span>
                ))}
              </div>

              <h3 style={{ fontSize: "17px", fontWeight: 700, color: "var(--foreground)", marginBottom: "6px" }}>
                {pkg.name}
              </h3>

              <div style={{ fontSize: "13px", color: "var(--gold)", fontWeight: 600, marginBottom: "12px" }}>
                ⏱️ {pkg.duration} &nbsp;•&nbsp; 🏷️ {pkg.startingPrice}
              </div>

              <p style={{ fontSize: "12.5px", color: "var(--text-dim)", lineHeight: "1.5", marginBottom: "14px", flex: 1 }}>
                {pkg.description}
              </p>

              <div style={{ fontSize: "12px", color: "var(--text-faint)", marginBottom: "18px", borderTop: "1px solid var(--line-soft)", paddingTop: "12px" }}>
                🏨 <strong>Recommended Stays:</strong> {pkg.resort}
              </div>

              <div style={{ display: "flex", gap: "10px" }}>
                <button
                  style={{
                    flex: 1,
                    padding: "9px 12px",
                    backgroundColor: "rgba(37, 211, 102, 0.12)",
                    border: "1px solid rgba(37, 211, 102, 0.3)",
                    color: "#25D366",
                    borderRadius: "8px",
                    fontSize: "12px",
                    fontWeight: 600,
                    cursor: "pointer",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    gap: "6px",
                  }}
                  onClick={() => handleSendWhatsApp(pkg.messageText)}
                >
                  <i className="ti ti-brand-whatsapp" />
                  <span>Send via WhatsApp</span>
                </button>

                <button
                  style={{
                    padding: "9px 14px",
                    backgroundColor: "var(--surface)",
                    border: "1px solid var(--line-soft)",
                    color: "var(--text-dim)",
                    borderRadius: "8px",
                    fontSize: "12px",
                    cursor: "pointer",
                  }}
                  onClick={() => handleCopy(pkg.messageText, pkg.name)}
                >
                  <i className="ti ti-copy" />
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Tab Content: COUPONS */}
      {activeTab === "coupons" && (
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))", gap: "16px" }}>
          {COUPONS.map((cp) => (
            <div
              key={cp.code}
              className="card"
              style={{
                padding: "20px",
                border: "1px dashed rgba(212,175,55,0.35)",
                position: "relative",
              }}
            >
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "8px" }}>
                <span style={{ fontSize: "18px", fontWeight: 700, color: "var(--gold)", letterSpacing: "1px", fontFamily: "monospace" }}>
                  {cp.code}
                </span>
                <span
                  style={{
                    fontSize: "11px",
                    backgroundColor: "rgba(63,191,127,0.12)",
                    color: "var(--green)",
                    padding: "2px 8px",
                    borderRadius: "12px",
                    fontWeight: 600,
                  }}
                >
                  {cp.discount}
                </span>
              </div>

              <div style={{ fontSize: "12.5px", color: "var(--text-dim)", marginBottom: "14px" }}>
                {cp.desc}
              </div>

              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", fontSize: "11.5px", color: "var(--text-faint)", borderTop: "1px solid var(--line-soft)", paddingTop: "10px" }}>
                <span>Used: <strong>{cp.used} times</strong></span>
                <span>Expires: <strong>{cp.expiry}</strong></span>
              </div>

              <button
                onClick={() => handleCopy(cp.code, cp.code)}
                style={{
                  width: "100%",
                  marginTop: "14px",
                  padding: "8px",
                  borderRadius: "8px",
                  backgroundColor: "rgba(212,175,55,0.1)",
                  border: "1px solid rgba(212,175,55,0.25)",
                  color: "var(--gold)",
                  fontSize: "12px",
                  fontWeight: 600,
                  cursor: "pointer",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  gap: "6px",
                }}
              >
                <i className="ti ti-copy" />
                <span>{copiedCode === cp.code ? "Code Copied!" : "Copy Voucher Code"}</span>
              </button>
            </div>
          ))}
        </div>
      )}

      {/* Modal: New Campaign */}
      {showNewModal && (
        <div
          style={{
            position: "fixed",
            inset: 0,
            backgroundColor: "rgba(0,0,0,0.75)",
            backdropFilter: "blur(4px)",
            zIndex: 9999,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            padding: "20px",
          }}
          onClick={() => setShowNewModal(false)}
        >
          <div
            className="card animate-in fade-in zoom-in-95 duration-200"
            style={{
              width: "100%",
              maxWidth: "500px",
              padding: "28px",
              border: "1px solid rgba(212,175,55,0.3)",
              boxShadow: "0 20px 50px rgba(0,0,0,0.6)",
            }}
            onClick={(e) => e.stopPropagation()}
          >
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "18px" }}>
              <h3 style={{ fontSize: "17px", fontWeight: 700, margin: 0, color: "var(--foreground)" }}>
                Launch New Marketing Campaign
              </h3>
              <button
                onClick={() => setShowNewModal(false)}
                style={{ background: "none", border: "none", color: "var(--text-faint)", cursor: "pointer", fontSize: "18px" }}
              >
                <i className="ti ti-x" />
              </button>
            </div>

            <form onSubmit={handleCreateCampaign}>
              <div style={{ marginBottom: "14px" }}>
                <label style={{ fontSize: "12px", fontWeight: 600, color: "var(--text-faint)", display: "block", marginBottom: "6px" }}>
                  CAMPAIGN TITLE
                </label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Andaman Island Romance Blast"
                  value={newTitle}
                  onChange={(e) => setNewTitle(e.target.value)}
                  style={{
                    width: "100%",
                    padding: "10px 12px",
                    borderRadius: "8px",
                    backgroundColor: "var(--surface)",
                    border: "1px solid var(--line-soft)",
                    color: "var(--foreground)",
                    fontSize: "13px",
                    boxSizing: "border-box",
                  }}
                />
              </div>

              <div style={{ marginBottom: "14px" }}>
                <label style={{ fontSize: "12px", fontWeight: 600, color: "var(--text-faint)", display: "block", marginBottom: "6px" }}>
                  FEATURED PACKAGE / DESTINATION
                </label>
                <input
                  type="text"
                  placeholder="e.g. 5D/4N Havelock & Neil Luxury Escape"
                  value={newPackage}
                  onChange={(e) => setNewPackage(e.target.value)}
                  style={{
                    width: "100%",
                    padding: "10px 12px",
                    borderRadius: "8px",
                    backgroundColor: "var(--surface)",
                    border: "1px solid var(--line-soft)",
                    color: "var(--foreground)",
                    fontSize: "13px",
                    boxSizing: "border-box",
                  }}
                />
              </div>

              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "12px", marginBottom: "14px" }}>
                <div>
                  <label style={{ fontSize: "12px", fontWeight: 600, color: "var(--text-faint)", display: "block", marginBottom: "6px" }}>
                    DISCOUNT / OFFER
                  </label>
                  <input
                    type="text"
                    placeholder="e.g. 15% OFF or ₹5,000 Flat"
                    value={newDiscount}
                    onChange={(e) => setNewDiscount(e.target.value)}
                    style={{
                      width: "100%",
                      padding: "10px 12px",
                      borderRadius: "8px",
                      backgroundColor: "var(--surface)",
                      border: "1px solid var(--line-soft)",
                      color: "var(--foreground)",
                      fontSize: "13px",
                      boxSizing: "border-box",
                    }}
                  />
                </div>
                <div>
                  <label style={{ fontSize: "12px", fontWeight: 600, color: "var(--text-faint)", display: "block", marginBottom: "6px" }}>
                    CHANNEL
                  </label>
                  <select
                    value={newChannel}
                    onChange={(e) => setNewChannel(e.target.value as any)}
                    style={{
                      width: "100%",
                      padding: "10px 12px",
                      borderRadius: "8px",
                      backgroundColor: "var(--surface)",
                      border: "1px solid var(--line-soft)",
                      color: "var(--foreground)",
                      fontSize: "13px",
                      boxSizing: "border-box",
                    }}
                  >
                    <option value="all">All Channels (WhatsApp + Social)</option>
                    <option value="whatsapp">WhatsApp Only</option>
                    <option value="instagram">Instagram / Meta</option>
                    <option value="email">Email Newsletter</option>
                  </select>
                </div>
              </div>

              <div style={{ marginBottom: "20px" }}>
                <label style={{ fontSize: "12px", fontWeight: 600, color: "var(--text-faint)", display: "block", marginBottom: "6px" }}>
                  EXCLUSIVE PERK / HIGHLIGHT
                </label>
                <input
                  type="text"
                  placeholder="e.g. Complimentary Scuba Dive + Private Beach Dinner"
                  value={newHighlight}
                  onChange={(e) => setNewHighlight(e.target.value)}
                  style={{
                    width: "100%",
                    padding: "10px 12px",
                    borderRadius: "8px",
                    backgroundColor: "var(--surface)",
                    border: "1px solid var(--line-soft)",
                    color: "var(--foreground)",
                    fontSize: "13px",
                    boxSizing: "border-box",
                  }}
                />
              </div>

              <div style={{ display: "flex", gap: "10px", justifyContent: "flex-end" }}>
                <button
                  type="button"
                  onClick={() => setShowNewModal(false)}
                  style={{
                    padding: "10px 16px",
                    backgroundColor: "var(--surface)",
                    border: "1px solid var(--line-soft)",
                    color: "var(--text-dim)",
                    borderRadius: "8px",
                    fontSize: "13px",
                    cursor: "pointer",
                  }}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="btn-gold"
                  style={{ padding: "10px 20px", fontSize: "13px", cursor: "pointer" }}
                >
                  Create Campaign
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
