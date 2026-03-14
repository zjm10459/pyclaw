const https = require('https');

const API_KEY = 'ctx7sk-84c3b19f-18bb-4d7c-a920-e6b7a36d03d0';

// 先搜索 LangChain 库
const searchQuery = 'langchain';
const userQuery = 'getting started';

const searchUrl = `https://context7.com/api/v2/libs/search?libraryName=${searchQuery}&query=${encodeURIComponent(userQuery)}`;

const options = {
  headers: {
    'Authorization': `Bearer ${API_KEY}`
  }
};

https.get(searchUrl, options, (res) => {
  let data = '';
  
  res.on('data', (chunk) => {
    data += chunk;
  });
  
  res.on('end', () => {
    console.log('搜索结果:');
    console.log(JSON.stringify(JSON.parse(data), null, 2));
  });
}).on('error', (err) => {
  console.error('错误:', err.message);
});
