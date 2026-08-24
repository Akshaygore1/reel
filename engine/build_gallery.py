#!/usr/bin/env python3
"""
Generates a standalone HTML Video Gallery for all reels in output/
Allows in-browser preview, instant playback, 1-click video download, and file deletion.
Strictly minimal card layout: video, title, meta pills, download button, delete button.
"""
import os, glob, subprocess

WORKSPACE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_DIR = os.path.join(WORKSPACE_DIR, "output")


def video_duration(path):
    """Read the actual MP4 duration for gallery metadata."""
    try:
        result = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", path],
            check=True, capture_output=True, text=True,
        )
        return f"{float(result.stdout.strip()):.1f}s"
    except (OSError, ValueError, subprocess.CalledProcessError):
        return "≤30s"

def build_gallery_html():
    mp4_files = sorted(glob.glob(os.path.join(OUTPUT_DIR, "*.mp4")))
    
    videos_data = []
    for mp4_path in mp4_files:
        filename = os.path.basename(mp4_path)
        slug = filename.replace("video_", "").replace(".mp4", "")
        title = slug.replace("_", " ").title()
        
        # File size
        size_bytes = os.path.getsize(mp4_path)
        size_mb = f"{size_bytes / (1024 * 1024):.2f} MB"
        
        # Relative path from index.html
        rel_video = f"output/{filename}"
        
        videos_data.append({
            "id": slug,
            "filename": filename,
            "title": title,
            "size": size_mb,
            "duration": video_duration(mp4_path),
            "video_src": rel_video,
        })
    
    cards_html = ""
    for item in videos_data:
        cards_html += f"""
    <div class="video-card" id="card-{item['id']}">
      <div class="video-wrapper">
        <video controls playsinline preload="metadata" loop>
          <source src="{item['video_src']}" type="video/mp4">
          Your browser does not support the video tag.
        </video>
      </div>
      <div class="card-body">
        <h2 class="card-title">{item['title']}</h2>
        <div class="card-meta">
          <span class="tag">9:16 Vertical</span>
          <span>{item['duration']}</span>
          <span>{item['size']}</span>
        </div>
        
        <div class="btn-row">
          <a href="{item['video_src']}" download="{item['filename']}" class="btn btn-download" title="Download video file">
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
              <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
              <polyline points="7 10 12 15 17 10"></polyline>
              <line x1="12" y1="15" x2="12" y2="3"></line>
            </svg>
            Download
          </a>
          <button class="btn btn-delete" onclick="deleteVideo('card-{item['id']}', '{item['filename']}')" title="Delete video from disk">
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
              <polyline points="3 6 5 6 21 6"></polyline>
              <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
              <line x1="10" y1="11" x2="10" y2="17"></line>
              <line x1="14" y1="11" x2="14" y2="17"></line>
            </svg>
            Delete
          </button>
        </div>
      </div>
    </div>
"""

    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>@buildebugship — System Design Video Gallery</title>
  <style>
    :root {{
      --bg: #090b10;
      --card-bg: #111622;
      --card-border: #1e293b;
      --card-hover: #334155;
      --text: #f8fafc;
      --muted: #94a3b8;
      --teal: #40e0d0;
      --teal-hover: #32c4b4;
      --red: #fb7185;
      --red-hover: #f43f5e;
      --green: #34d153;
      --blue: #60a5fa;
      --amber: #f5a623;
    }}
    * {{
      box-sizing: border-box;
      margin: 0;
      padding: 0;
    }}
    body {{
      background-color: var(--bg);
      color: var(--text);
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
      min-height: 100vh;
      padding: 40px 24px 60px 24px;
      line-height: 1.5;
    }}
    .header {{
      max-width: 1280px;
      margin: 0 auto 36px auto;
      display: flex;
      flex-direction: column;
      align-items: center;
      text-align: center;
      border-bottom: 1px solid var(--card-border);
      padding-bottom: 28px;
    }}
    .brand-badge {{
      display: inline-flex;
      align-items: center;
      gap: 8px;
      padding: 6px 16px;
      background: rgba(251, 113, 133, 0.12);
      border: 1px solid rgba(251, 113, 133, 0.4);
      border-radius: 999px;
      color: var(--red);
      font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
      font-size: 14px;
      font-weight: 600;
      margin-bottom: 16px;
    }}
    .brand-badge .dot {{
      width: 8px;
      height: 8px;
      border-radius: 50%;
      background-color: var(--red);
      box-shadow: 0 0 10px var(--red);
    }}
    h1 {{
      font-size: 32px;
      font-weight: 800;
      letter-spacing: -0.02em;
      margin-bottom: 8px;
      background: linear-gradient(135deg, #ffffff 40%, var(--teal) 100%);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
    }}
    .subtitle {{
      color: var(--muted);
      font-size: 15px;
      max-width: 600px;
    }}
    .stats-bar {{
      display: flex;
      flex-wrap: wrap;
      justify-content: center;
      gap: 24px;
      margin-top: 18px;
      font-size: 13px;
      color: var(--muted);
      font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
    }}
    .stats-bar span {{
      color: var(--teal);
      font-weight: 600;
    }}
    .gallery-grid {{
      max-width: 1380px;
      margin: 0 auto;
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
      gap: 28px;
    }}
    .video-card {{
      background: var(--card-bg);
      border: 1px solid var(--card-border);
      border-radius: 16px;
      overflow: hidden;
      display: flex;
      flex-direction: column;
      transition: transform 0.25s cubic-bezier(0.4, 0, 0.2, 1), 
                  opacity 0.25s cubic-bezier(0.4, 0, 0.2, 1), 
                  border-color 0.2s ease, 
                  box-shadow 0.2s ease;
    }}
    .video-card:hover {{
      transform: translateY(-4px);
      border-color: rgba(64, 224, 208, 0.4);
      box-shadow: 0 12px 30px rgba(0, 0, 0, 0.4);
    }}
    .video-card.deleting {{
      opacity: 0;
      transform: scale(0.9) translateY(10px);
      pointer-events: none;
    }}
    .video-wrapper {{
      position: relative;
      width: 100%;
      background: #000;
      aspect-ratio: 9 / 16;
      display: flex;
      align-items: center;
      justify-content: center;
    }}
    .video-wrapper video {{
      width: 100%;
      height: 100%;
      object-fit: cover;
      display: block;
    }}
    .card-body {{
      padding: 20px;
      display: flex;
      flex-direction: column;
      flex-grow: 1;
    }}
    .card-title {{
      font-size: 17px;
      font-weight: 700;
      margin-bottom: 6px;
      color: #fff;
    }}
    .card-meta {{
      display: flex;
      align-items: center;
      gap: 10px;
      font-size: 12px;
      color: var(--muted);
      font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
      margin-bottom: 18px;
    }}
    .card-meta .tag {{
      background: rgba(96, 165, 250, 0.15);
      color: var(--blue);
      padding: 2px 8px;
      border-radius: 4px;
      font-weight: 600;
    }}
    .btn-row {{
      display: flex;
      gap: 10px;
      margin-top: auto;
    }}
    .btn {{
      display: inline-flex;
      align-items: center;
      justify-content: center;
      gap: 8px;
      padding: 10px 16px;
      border-radius: 8px;
      font-size: 13px;
      font-weight: 600;
      text-decoration: none;
      cursor: pointer;
      border: none;
      transition: all 0.15s ease;
      flex: 1;
    }}
    .btn-download {{
      background: var(--teal);
      color: #090b10;
    }}
    .btn-download:hover {{
      background: var(--teal-hover);
      box-shadow: 0 0 14px rgba(64, 224, 208, 0.35);
    }}
    .btn-delete {{
      background: rgba(251, 113, 133, 0.12);
      color: var(--red);
      border: 1px solid rgba(251, 113, 133, 0.35);
    }}
    .btn-delete:hover {{
      background: var(--red);
      color: #090b10;
      border-color: var(--red);
      box-shadow: 0 0 14px rgba(251, 113, 133, 0.4);
    }}
    .empty-state {{
      max-width: 500px;
      margin: 80px auto;
      text-align: center;
      padding: 40px 24px;
      background: var(--card-bg);
      border: 1px dashed var(--card-border);
      border-radius: 16px;
      color: var(--muted);
    }}
    .empty-state h3 {{
      color: #fff;
      margin-bottom: 8px;
      font-size: 20px;
    }}
    .toast {{
      position: fixed;
      bottom: 24px;
      right: 24px;
      background: var(--card-bg);
      color: var(--text);
      border: 1px solid var(--card-border);
      font-weight: 600;
      padding: 14px 22px;
      border-radius: 10px;
      font-size: 14px;
      box-shadow: 0 10px 30px rgba(0,0,0,0.6);
      opacity: 0;
      transform: translateY(16px);
      transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
      pointer-events: none;
      z-index: 100;
      display: flex;
      align-items: center;
      gap: 10px;
    }}
    .toast.show {{
      opacity: 1;
      transform: translateY(0);
    }}
    .toast.toast-success {{
      border-color: rgba(52, 211, 153, 0.5);
      color: var(--green);
    }}
    .toast.toast-danger {{
      border-color: rgba(251, 113, 133, 0.5);
      color: var(--red);
    }}
    .toast.toast-warning {{
      border-color: rgba(245, 166, 35, 0.5);
      color: var(--amber);
    }}
  </style>
</head>
<body>

  <header class="header">
    <div class="brand-badge">
      <span class="dot"></span>
      @buildebugship
    </div>
    <h1>System Design Blueprint Video Gallery</h1>
    <p class="subtitle">Autonomous 9:16 vertical video reels with vector blueprint animations, procedural game SFX, and zero voiceover.</p>
    <div class="stats-bar">
      <div>Total Videos: <span id="total-videos-count">{len(videos_data)}</span></div>
      <div>Profile: <span>720×1280 @ 30fps (up to 30s)</span></div>
      <div>Soundtrack: <span>Procedural Game SFX + Lo-Fi Synth</span></div>
    </div>
  </header>

  <main class="gallery-grid" id="galleryGrid">
{cards_html}
  </main>

  <div id="toast" class="toast"></div>

  <script>
    function showToast(message, type = 'success') {{
      const toast = document.getElementById('toast');
      toast.textContent = message;
      toast.className = 'toast toast-' + type + ' show';
      setTimeout(() => {{
        toast.classList.remove('show');
      }}, 3000);
    }}

    function updateVideoCount() {{
      const remainingCards = document.querySelectorAll('.video-card').length;
      const countEl = document.getElementById('total-videos-count');
      if (countEl) {{
        countEl.textContent = remainingCards;
      }}
      if (remainingCards === 0) {{
        const grid = document.getElementById('galleryGrid');
        if (grid) {{
          grid.innerHTML = `
            <div class="empty-state">
              <h3>No Videos Found</h3>
              <p>All videos have been deleted or none exist in output/. Run <code>python3 generate.py --preset all</code> to generate reels.</p>
            </div>
          `;
        }}
      }}
    }}

    async function deleteVideo(cardId, filename) {{
      const confirmed = confirm(`Are you sure you want to delete ${filename}?\\nThis will permanently remove the video file.`);
      if (!confirmed) return;

      const card = document.getElementById(cardId);
      if (card) {{
        card.classList.add('deleting');
      }}

      try {{
        const endpoint = window.location.protocol === 'file:' 
          ? 'http://localhost:8000/api/delete' 
          : '/api/delete';

        const res = await fetch(endpoint, {{
          method: 'POST',
          headers: {{ 'Content-Type': 'application/json' }},
          body: JSON.stringify({{ filename: filename }})
        }});

        if (res.ok) {{
          const data = await res.json();
          if (data.success) {{
            setTimeout(() => {{
              if (card) card.remove();
              updateVideoCount();
              showToast(`🗑️ Successfully deleted ${filename}`, 'danger');
            }}, 250);
            return;
          }}
        }}
        throw new Error('API delete failed');
      }} catch (err) {{
        console.warn('Server endpoint error, performing UI removal:', err);
        setTimeout(() => {{
          if (card) card.remove();
          updateVideoCount();
          showToast(`🗑️ Removed ${filename} from view (run 'python3 server.py' to delete from disk)`, 'warning');
        }}, 250);
      }}
    }}
  </script>
</body>
</html>
"""

    index_path = os.path.join(WORKSPACE_DIR, "index.html")
    gallery_path = os.path.join(WORKSPACE_DIR, "gallery.html")
    
    with open(index_path, "w", encoding="utf-8") as f:
        f.write(html_content)
    with open(gallery_path, "w", encoding="utf-8") as f:
        f.write(html_content)
    
    print(f"✅ Generated HTML Gallery at: {index_path} and {gallery_path}")
    return index_path

if __name__ == "__main__":
    build_gallery_html()
