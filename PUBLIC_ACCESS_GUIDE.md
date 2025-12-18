# Making Digital Twins Explorer Public

You have **2 working approaches** to make your Digital Twins data publicly accessible:

## ✅ Approach 1: Use Your Node-RED API (EASIEST - Already Working!)

Your Node-RED endpoint is **already public** and working:
- **URL**: https://adt-node.onrender.com/api/telemetry
- **Status**: ✅ Live and accessible
- **Authentication**: None required

### Quick Test:
```bash
curl https://adt-node.onrender.com/api/telemetry
```

### Create Simple Public Viewer:
Since Node-RED is already public, just create a simple HTML dashboard that fetches from it:

```html
<!DOCTYPE html>
<html>
<head>
    <title>Farm Digital Twin - Live</title>
    <script>
        async function loadData() {
            const response = await fetch('https://adt-node.onrender.com/api/telemetry');
            const data = await response.json();
            document.getElementById('data').textContent = JSON.stringify(data, null, 2);
        }
        setInterval(loadData, 5000);  // Refresh every 5 seconds
        loadData();
    </script>
</head>
<body>
    <h1>🌾 Live Farm Data</h1>
    <pre id="data">Loading...</pre>
</body>
</html>
```

---

## 🚀 Approach 2: Deploy Azure Function Proxy (More Features)

I've created `DigitalTwinsProxy` Azure Function that provides full Digital Twins API access without authentication.

### Deploy the Proxy:

```bash
# 1. Navigate to azure-functions directory
cd /home/hs32/Documents/Projects/adt/azure-functions

# 2. Deploy to Azure
func azure functionapp publish <your-function-app-name>

# 3. Test it
curl "https://<your-function-app>.azurewebsites.net/api/dt?operation=listTwins"
```

### API Endpoints:

| Operation | URL | Description |
|-----------|-----|-------------|
| List All Twins | `/api/dt?operation=listTwins` | Get all digital twins |
| Get Specific Twin | `/api/dt?operation=getTwin&twinId=zone_A` | Get one twin |
| Query Twins | `/api/dt?operation=query&query=SELECT * FROM digitaltwins` | Custom query |
| List Models | `/api/dt?operation=listModels` | Get all models |
| List Relationships | `/api/dt?operation=listRelationships&twinId=zone_A` | Get twin relationships |

---

## 🌐 Deploy Digital Twins Explorer to Render/Railway

Once you have a public API (either Node-RED or Azure Function), you can:

### Option A: Use Node-RED Directly
Deploy a simple viewer that just shows your Node-RED data (fastest!)

### Option B: Modify Explorer to Use Proxy
1. Stop fighting with the old explorer Docker build
2. Modify the explorer's API client to call your proxy instead of Azure directly
3. Deploy the modified explorer to Render/Railway

---

## 📊 Recommended Solution:

**Use Node-RED (Approach 1)** because:
- ✅ Already working and public
- ✅ No Azure Function deployment needed
- ✅ No authentication issues
- ✅ Simple HTML viewer is enough
- ✅ Can deploy to GitHub Pages for free

### Next Steps:

1. Create a simple HTML/React dashboard
2. Point it to `https://adt-node.onrender.com/api/telemetry`
3. Deploy to:
   - **GitHub Pages** (free, easiest)
   - **Vercel** (free, modern)
   - **Netlify** (free, simple)
   - **Render** (free, full control)

No need to fight with the 4-year-old Digital Twins Explorer!

---

## 🛠️ If You Still Want the Full Explorer:

The official Azure Digital Twins Explorer requires authentication. To make it "public":

1. **Option A**: Create a shared Azure AD account for read-only access
2. **Option B**: Use the proxy approach above and modify explorer source
3. **Option C**: Build a custom lightweight viewer (recommended)

Let me know which approach you want to proceed with!
