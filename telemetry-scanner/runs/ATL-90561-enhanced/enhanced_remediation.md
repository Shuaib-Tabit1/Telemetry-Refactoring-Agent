OpenTelemetry spans for inbound HTTP requests currently miss two important attributes:
• `http.referer` – the value of the incoming `Referer` request header  
• `http.response.redirect_location` – the value of the `Location` header sent back with 3xx responses  

The global `ScmHttpApplication` already runs for every request inside the classic ASP.NET stack, which is also where the OpenTelemetry `Activity` for the request is active (`Activity.Current`).  
By enriching that `Activity` before the request is processed (for the *Referer*) and right after the response is written (for the redirect *Location*), we guarantee the two attributes are always present when the corresponding header exists.