---
categories:
- javascript
date: 2025-02-08 15:07 +0800
id: be238cab-22c7-4e2f-97fe-23b20bc30367
layout: post
tags:
- javascript
title: Chrome Extension Development Notes
---

### Change url before load

#### Tried methods

##### 1. Change the value of `window.location.href` after page loaded (slow)

```javascript
// content js
function getTrulyUrl() {
    const param = hostParams[window.location.host];
    if (param) {
        return parse()[param];
    }
}

function justGo() {
    const turelyUrl = getTrulyUrl();
    if (turelyUrl) {
        window.location.href = turelyUrl;
    }
}
```



##### 2. Use `chrome.tabs.onUpdated.addListener` api (worked)

```javascript
// background.js
chrome.tabs.onUpdated.addListener(
    function(tabId, changeInfo, tab) {
        const redirectUrl = getRedirectUrl(tab.url);
        if (redirectUrl) {
            chrome.tabs.update(tab.id, {url: redirectUrl});              
        }
    }
  );
```



##### 3. Use `chrome.webRequest.onBeforeRequest.addListener` api (not work)

**Note: manifest v3 not support `blocking` for this api, and v2 is not support anymore since 2024**

```javascript
// background.js
chrome.webRequest.onBeforeRequest.addListener(
    function (details) {
        const url = getRedirectUrl(details.url);
        if (url) {
            return {
                redirectUrl: url
            }
        }
    },

    { urls: ["<all_urls>"] },
    ["blocking"]
);
```



##### 4. Use `declarative_net_request` api (not work)

It just doesn’t work and is not easy to use (dynamic redirect support is not good enough).

```javascript
[
    {
        "id": 1,
        "priority": 1,
        "action": {
          "type": "redirect",
          "redirect": {
            "regexSubstitution": "\\1"
          }
        },
        "condition": {
          "regexFilter": "^https://link.zhihu.com/?target=(.*)",
          "resourceTypes": [
            "main_frame"
          ]
        }
      }
]
```



##### 5. Use `webNavigation` api (final)

```javascript
// background.js
chrome.webNavigation.onBeforeNavigate.addListener((details) => {
    const url = getRedirectUrl(details.url);
    if (url) {
        chrome.tabs.update(details.tabId, {
            url: url
        });
    }
})
```



See: https://stackoverflow.com/questions/7387152/modify-url-location-in-chrome-extensions-stop-the-initial-request



### Reference

1. [扩展程序 / 开始使用 \| Get started \| Chrome for Developers](https://developer.chrome.com/docs/extensions/get-started?hl=zh-cn "扩展程序 / 开始使用  \|  Get started  \|  Chrome for Developers")