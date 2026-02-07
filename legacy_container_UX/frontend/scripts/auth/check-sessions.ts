
async function check() {
  try {
    // Login
    const loginRes = await fetch('http://localhost:8000/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: 'username=enterprise@test.com&password=test123'
    });
    const loginData = await loginRes.json();
    const token = loginData.access_token;
    console.log('Token acquired');

    // Decode token
    const payloadPart = token.split('.')[1];
    const payloadStr = Buffer.from(payloadPart, 'base64').toString();
    const payload = JSON.parse(payloadStr);
    console.log('Token Payload:', payload);
    const userId = payload.sub;
    console.log('User ID from token:', userId);

    // Fetch UserSession (which contains sessions)
    const url = `http://localhost:8000/usersessions/${userId}/resources`;
    console.log(`Fetching: ${url}`);
    
    const sessionsRes = await fetch(url, {
      headers: { 'Authorization': `Bearer ${token}` }
    });
    
    if (sessionsRes.ok) {
      const data = await sessionsRes.json();
      console.log('Resources Data:', JSON.stringify(data, null, 2));
      
      if (data.resources) {
        console.log(`Found ${data.resources.length} resources.`);
      } else {
        console.log('No resources array in response.');
      }
    } else {
      console.log('Failed to fetch sessions:', sessionsRes.status, await sessionsRes.text());
    }
  } catch (e) {
    console.error(e);
  }
}

check();
