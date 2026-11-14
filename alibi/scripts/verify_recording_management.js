async page => {
 const errors=[]; page.on('pageerror',e=>errors.push(e.message));
 await page.goto('http://127.0.0.1:8765');
 await page.getByRole('button',{name:'Record & edit',exact:true}).click();
 await page.getByLabel('Import audio',{exact:true}).setInputFiles('work/delete-test.wav');
 await page.getByRole('heading',{name:'Recording & editor',exact:true}).waitFor();
 page.once('dialog',d=>d.accept('Delete QA'));
 await page.getByRole('button',{name:/Create folder/}).click();
 await page.waitForFunction(()=>document.querySelector('[aria-label="Recording folder filter"] option[value]'));
 await page.getByLabel('Assign selected recording folder',{exact:true}).selectOption({label:'Delete QA'});
 const before=await page.getByText('delete-test',{exact:false}).count();
 page.once('dialog',d=>d.accept());
 await page.keyboard.press('Delete');
 await page.waitForTimeout(400);
 const after=await page.getByRole('heading',{name:'Recording & editor',exact:true}).count();
 if(after!==0)throw Error('Delete key did not remove selected recording');
 if(errors.length)throw Error(errors.join('; '));
 return {pass:true,before,after,folderCreated:true,deleteKeyConfirmed:true};
}
