<%namespace name="layout" file="email-layout"/>
<%layout:line>Hi there,</%layout:line>
<%layout:line>We received a request from you to ${intent}. Please use the link below to do so:</%layout:line>
<%layout:button href="${authlink}">${intent_button}</%layout:button>
<%layout:line>If you didn't request this email, please just ignore it or <%layout:link href="mailto:team@gitfund.io">contact us</%layout:link> if you believe someone might be trying to hack into your account. Thank you.</%layout:line>