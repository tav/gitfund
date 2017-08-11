<%namespace name="layout" file="email-layout"/>
<%layout:line>Hi there,</%layout:line>
<%layout:line>There was an error processing your GitFund payment.</%layout:line>
<%layout:line>Please resolve the issue soon. We'll try charging your card again over the next two weeks. You can use the link below to update your payment information:</%layout:line>
<%layout:button href="${authlink}">Update Payment Info</%layout:button>
<%layout:line>If you feel there's been a mistake or have any questions, please email us at <%layout:link href="mailto:team@gitfund.io">team@gitfund.io</%layout:link>. Thanks!</%layout:line>