
// import { fetch } from 'undici';

async function checkUserSession() {
  const userId = 'user_enterprise';
  const url = `http://localhost:8000/usersessions/${userId}`;
  
  console.log(`Fetching: ${url}`);
  try {
    const res = await fetch(url);
    if (!res.ok) {
      console.error(`Failed: ${res.status} ${res.statusText}`);
      const text = await res.text();
      console.error(text);
      return;
    }
    
    const data = await res.json();
    console.log('User Session:', JSON.stringify(data, null, 2));
  } catch (e) {
    console.error('Error:', e);
  }
}

checkUserSession();
