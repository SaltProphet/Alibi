async page => {
 await page.goto('http://127.0.0.1:8875');await page.getByLabel('Text to speak',{exact:true}).fill('The audio studio still works.');await page.getByRole('button',{name:'Generate speech',exact:true}).last().click();
 await page.waitForFunction(()=>document.querySelector('.selected-player audio'),{},{timeout:180000});
 await page.getByRole('button',{name:'Add to arrangement',exact:true}).click();await page.getByLabel('Session name',{exact:true}).fill('Video change audio regression');
 await page.getByRole('button',{name:'Save session',exact:true}).click();await page.getByRole('button',{name:'Export mixed WAV',exact:true}).click();await page.getByRole('link',{name:'Download mixed WAV ↗',exact:true}).waitFor();
 const wav=await page.getByRole('link',{name:'Download mixed WAV ↗',exact:true}).getAttribute('href');
 await page.getByRole('button',{name:'Play arrangement',exact:true}).click();await page.waitForTimeout(600);await page.getByRole('button',{name:'Stop arrangement',exact:true}).click();
 await page.getByRole('button',{name:'Record & edit',exact:true}).click();await page.getByRole('heading',{name:'Recording & editor',exact:true}).waitFor();
 const recordVisible=await page.getByRole('button',{name:'Record microphone',exact:true}).isVisible();
 return {pass:true,generate:true,arrange:true,saveSession:true,mixWav:wav,arrangementPlayback:true,editorVisible:true,recordControlVisible:recordVisible,physicalMicrophone:'not tested'};
}
