export const prerender = false;

const DEEPSEEK_API = 'https://api.deepseek.com/chat/completions';

export async function POST({ request }) {
  const apiKey = (typeof process !== 'undefined' && process.env.DEEPSEEK_API_KEY)
    || (typeof import.meta !== 'undefined' && import.meta.env.DEEPSEEK_API_KEY);

  if (!apiKey) {
    return new Response(JSON.stringify({ error: 'API key 未配置' }), {
      status: 500, headers: { 'Content-Type': 'application/json' },
    });
  }

  const { messages } = await request.json();

  if (!messages || !Array.isArray(messages) || messages.length === 0) {
    return new Response(JSON.stringify({ error: '消息不能为空' }), {
      status: 400, headers: { 'Content-Type': 'application/json' },
    });
  }

  const systemPrompt = {
    role: 'system',
    content: `你是这个个人网站的智能助手。你的风格是：温柔、耐心、逻辑清晰。
回答问题时简洁有温度，不啰嗦。用中文回答。`,
  };

  const body = JSON.stringify({
    model: 'deepseek-chat',
    messages: [systemPrompt, ...messages],
    stream: true,
    temperature: 0.7,
  });

  try {
    const response = await fetch(DEEPSEEK_API, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${apiKey}`,
      },
      body,
    });

    if (!response.ok) {
      const err = await response.text();
      return new Response(JSON.stringify({ error: `DeepSeek API 错误: ${response.status}` }), {
        status: response.status, headers: { 'Content-Type': 'application/json' },
      });
    }

    // 直接透传 SSE 流
    return new Response(response.body, {
      headers: {
        'Content-Type': 'text/event-stream',
        'Cache-Control': 'no-cache',
        'Connection': 'keep-alive',
      },
    });
  } catch (err) {
    return new Response(JSON.stringify({ error: '请求失败: ' + err.message }), {
      status: 500, headers: { 'Content-Type': 'application/json' },
    });
  }
}
