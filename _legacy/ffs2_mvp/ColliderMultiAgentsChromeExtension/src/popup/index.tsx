/**
 * Popup - Simple status/quick actions
 */

import React from "react"

export default function Popup() {
  const openSidepanel = () => {
    chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
      if (tabs[0]?.id) {
        chrome.sidePanel.open({ tabId: tabs[0].id })
      }
    })
    window.close()
  }

  return (
    <div style={styles.container}>
      <h2 style={styles.title}>⚡ Collider</h2>
      <p style={styles.desc}>Multi-Agent Chrome Extension</p>
      <button onClick={openSidepanel} style={styles.btn}>
        Open Sidepanel
      </button>
    </div>
  )
}

const styles: Record<string, React.CSSProperties> = {
  container: {
    width: "240px",
    padding: "20px",
    background: "#1f2937",
    color: "#f9fafb",
    fontFamily: "system-ui, sans-serif",
    textAlign: "center",
  },
  title: {
    margin: "0 0 8px 0",
    fontSize: "20px",
  },
  desc: {
    margin: "0 0 16px 0",
    fontSize: "14px",
    color: "#9ca3af",
  },
  btn: {
    width: "100%",
    padding: "10px",
    background: "#4f46e5",
    color: "white",
    border: "none",
    borderRadius: "6px",
    cursor: "pointer",
    fontSize: "14px",
  },
}
