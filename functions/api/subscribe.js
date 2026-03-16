export async function onRequestPost(context) {
  try {
    const body = await context.request.json();
    const email = body.email;
    if (!email || !email.includes('@')) {
      return new Response(JSON.stringify({error: 'Invalid email'}), {status: 400});
    }

    // Store in KV (if available) or just forward notification
    // For now: send a simple notification via fetch to the VPS
    // The VPS webhook will handle CRM + email
    try {
      await fetch('https://charlotte2.srv1346966.cloud/webhook/subscribe', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({email, source: 'monarchxcapital.com', ts: new Date().toISOString()})
      });
    } catch(e) {
      // VPS webhook failed — still return success to user
      console.error('VPS webhook failed:', e);
    }

    return new Response(JSON.stringify({success: true}), {
      status: 200,
      headers: {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'}
    });
  } catch(e) {
    return new Response(JSON.stringify({error: 'Server error'}), {status: 500});
  }
}

export async function onRequestOptions() {
  return new Response(null, {
    headers: {
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'POST, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type'
    }
  });
}
